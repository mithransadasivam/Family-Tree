"""People search inside a community: only trees their owners shared, only a basic card per person."""
from datetime import date

from django.db.models import Q

from family_members.models import FamilyMember
from relationships.models import Relationship

# Same lists as the website (web/src/graph.ts): a link "X is the Father of Y" says X is male.
MALE_TYPES = {
    'Father', 'Stepfather', 'Step Father', 'Grandfather', 'Son', 'Stepson', 'Step Son', 'Adopted Son',
    'Grandson', 'Brother', 'Step Brother', 'Adopted Brother', 'Husband', 'Fiance', 'Uncle',
    'Father-in-Law', 'Son-in-Law', 'Brother-in-Law',
}
FEMALE_TYPES = {
    'Mother', 'Stepmother', 'Step Mother', 'Grandmother', 'Daughter', 'Stepdaughter', 'Step Daughter',
    'Adopted Daughter', 'Granddaughter', 'Sister', 'Step Sister', 'Adopted Sister', 'Wife', 'Fiancee',
    'Aunt', 'Mother-in-Law', 'Daughter-in-Law', 'Sister-in-Law',
}
GENDERS = ('male', 'female', 'other')
MAX_PAGE = 50


def years_before(today, years):
    try:
        return today.replace(year=today.year - years)
    except ValueError:  # 29 February
        return today.replace(year=today.year - years, day=28)


def age_of(member, today):
    if member.death_date or not member.birth_date:
        return None
    b = member.birth_date
    return today.year - b.year - ((today.month, today.day) < (b.month, b.day))


def inferred_genders(tree_ids):
    out = {}
    rels = Relationship.objects.filter(
        tree_id__in=tree_ids,
        relationship_type__type_name__in=MALE_TYPES | FEMALE_TYPES,
    ).values_list('member_1_id', 'relationship_type__type_name')
    for member_id, type_name in rels:
        out[member_id] = 'male' if type_name in MALE_TYPES else 'female'
    return out


def parse_int(value, low=0, high=130):
    if value in (None, ''):
        return None
    try:
        n = int(value)
    except (TypeError, ValueError):
        raise ValueError('Ages must be whole numbers')
    if not low <= n <= high:
        raise ValueError(f'Ages must be between {low} and {high}')
    return n


def search_people(community, params, today=None):
    """Returns (total, results). Raises ValueError for bad filter values."""
    today = today or date.today()
    tree_ids = list(community.shared_trees.values_list('tree_id', flat=True))
    qs = FamilyMember.objects.filter(tree_id__in=tree_ids)

    for token in (params.get('q') or '').split()[:5]:
        qs = qs.filter(Q(first_name__icontains=token) | Q(last_name__icontains=token))

    age = parse_int(params.get('age'))
    age_min = parse_int(params.get('age_min'))
    age_max = parse_int(params.get('age_max'))
    if age is not None:
        age_min = age_max = age
    if age_min is not None and age_max is not None and age_min > age_max:
        raise ValueError('The minimum age is above the maximum age')
    if age_min is not None or age_max is not None:
        qs = qs.filter(death_date__isnull=True, birth_date__isnull=False)  # ages are for living people
        if age_min is not None:
            qs = qs.filter(birth_date__lte=years_before(today, age_min))
        if age_max is not None:
            # Still age_max today means born after (today - (age_max + 1) years).
            qs = qs.filter(birth_date__gt=years_before(today, age_max + 1))

    living = params.get('living')
    if living == 'yes':
        qs = qs.filter(death_date__isnull=True)
    elif living == 'no':
        qs = qs.filter(death_date__isnull=False)

    wanted = [g for g in (params.get('gender') or '').split(',') if g in GENDERS]
    members = list(qs.order_by('first_name', 'last_name', 'id'))
    guesses = inferred_genders(tree_ids) if members else {}

    rows = []
    for m in members:
        gender = m.gender or guesses.get(m.id, '')
        if wanted and gender not in wanted:
            continue
        rows.append({
            'id': m.id,
            'first_name': m.first_name,
            'last_name': m.last_name,
            'gender': gender,
            'age': age_of(m, today),
            'deceased': bool(m.death_date),
            # A private number is never shown to the community.
            'phone': m.phone if m.phone_public else '',
        })

    try:
        offset = max(0, int(params.get('offset') or 0))
        limit = min(MAX_PAGE, max(1, int(params.get('limit') or MAX_PAGE)))
    except ValueError:
        raise ValueError('limit and offset must be numbers')
    return len(rows), rows[offset:offset + limit]
