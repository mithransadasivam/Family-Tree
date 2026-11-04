package com.familytree.familytree.ui.screens

import com.familytree.familytree.data.models.FamilyMember
import com.familytree.familytree.data.models.Relationship

// Reciprocal relationship labels, ported from the web app (web/src/graph.ts) so both clients
// describe a link the same way. A stored relationship reads "member_1 IS <type> OF member_2",
// so the type is the right label for member_1 as seen from member_2 - and member_2 needs the
// inverse term (Father <-> Son/Daughter, Husband <-> Wife, ...) when viewed from member_1.
// English only: the stored type is the canonical English name (see RelationshipTerms.kt).

enum class KnownGender { MALE, FEMALE }

// type -> what member_2 is to member_1 for a link of that type. Neutral labels that appear in
// genderedInverse are specialised by member_2's gender when it is known.
private val inverseOf: Map<String, String> = buildMap {
    fun def(names: List<String>, inverse: String) = names.forEach { put(it, inverse) }
    def(listOf("Father", "Mother"), "Child")
    def(listOf("Step Father", "Step Mother", "Stepfather", "Stepmother"), "Stepchild")
    def(listOf("Son", "Daughter"), "Parent")
    def(listOf("Step Son", "Step Daughter", "Stepson", "Stepdaughter"), "Step-parent")
    def(listOf("Adopted Son", "Adopted Daughter"), "Adoptive parent")
    def(listOf("Grandfather", "Grandmother"), "Grandchild")
    def(listOf("Grandson", "Granddaughter"), "Grandparent")
    def(listOf("Brother", "Sister"), "Sibling")
    def(listOf("Step Brother", "Step Sister"), "Step-sibling")
    def(listOf("Adopted Brother", "Adopted Sister"), "Adopted sibling")
    def(listOf("Husband", "Wife"), "Husband / wife")
    def(listOf("Spouse"), "Spouse")
    def(listOf("Partner"), "Partner")
    def(listOf("Fiance", "Fiancee"), "Fiance / fiancee")
    def(listOf("Father-in-Law", "Mother-in-Law"), "Child-in-law")
    def(listOf("Son-in-Law", "Daughter-in-Law"), "Parent-in-law")
    def(listOf("Brother-in-Law", "Sister-in-Law"), "Sibling-in-law")
    def(listOf("Uncle", "Aunt"), "Nephew / niece")
    def(listOf("Cousin"), "Cousin")
    def(listOf("Guardian"), "Ward")
}

// Neutral inverse label -> (male term, female term).
private val genderedInverse: Map<String, Pair<String, String>> = mapOf(
    "Child" to ("Son" to "Daughter"),
    "Parent" to ("Father" to "Mother"),
    "Sibling" to ("Brother" to "Sister"),
    "Step-sibling" to ("Step Brother" to "Step Sister"),
    "Adopted sibling" to ("Adopted Brother" to "Adopted Sister"),
    "Grandchild" to ("Grandson" to "Granddaughter"),
    "Grandparent" to ("Grandfather" to "Grandmother"),
    "Husband / wife" to ("Husband" to "Wife"),
    "Fiance / fiancee" to ("Fiance" to "Fiancee"),
    "Nephew / niece" to ("Nephew" to "Niece"),
    "Stepchild" to ("Step Son" to "Step Daughter"),
    "Step-parent" to ("Step Father" to "Step Mother"),
    "Adoptive parent" to ("Adoptive Father" to "Adoptive Mother"),
    "Child-in-law" to ("Son-in-Law" to "Daughter-in-Law"),
    "Parent-in-law" to ("Father-in-Law" to "Mother-in-Law"),
    "Sibling-in-law" to ("Brother-in-Law" to "Sister-in-Law"),
)

// Types that tell us the gender of member_1 (the person being described).
private val maleTypes = setOf(
    "Father", "Stepfather", "Step Father", "Grandfather", "Son", "Stepson", "Step Son", "Adopted Son",
    "Grandson", "Brother", "Step Brother", "Adopted Brother", "Husband", "Fiance", "Uncle",
    "Father-in-Law", "Son-in-Law", "Brother-in-Law",
)
private val femaleTypes = setOf(
    "Mother", "Stepmother", "Step Mother", "Grandmother", "Daughter", "Stepdaughter", "Step Daughter",
    "Adopted Daughter", "Granddaughter", "Sister", "Step Sister", "Adopted Sister", "Wife", "Fiancee",
    "Aunt", "Mother-in-Law", "Daughter-in-Law", "Sister-in-Law",
)

/**
 * Who is male or female. A person's own recorded gender wins; otherwise it is inferred from how
 * they were described in a link ("X is the Father of Y" says X is male). Anyone with neither
 * stays unknown and is described with neutral words ("Child", "Sibling").
 */
fun inferGenders(
    relationships: List<Relationship>,
    members: List<FamilyMember> = emptyList(),
): Map<Int, KnownGender> {
    val out = HashMap<Int, KnownGender>()
    relationships.forEach { rel ->
        val name = rel.relationship_type_name
        when {
            name in maleTypes -> out[rel.member_1] = KnownGender.MALE
            name in femaleTypes -> out[rel.member_1] = KnownGender.FEMALE
        }
    }
    members.forEach { m ->
        when (m.gender?.lowercase()) {
            "male" -> out[m.id] = KnownGender.MALE
            "female" -> out[m.id] = KnownGender.FEMALE
            "other" -> out.remove(m.id)
        }
    }
    return out
}

/** What the other person in [rel] is to [selfId], as a label to show on selfId's page. */
fun relationshipLabelFor(
    rel: Relationship,
    selfId: Int,
    genders: Map<Int, KnownGender> = emptyMap(),
): String {
    val name = rel.relationship_type_name
    val selfIsFirst = rel.member_1 == selfId
    val inverse = inverseOf[name] ?: return if (selfIsFirst) "$name of" else name
    // self is member_2, so the stored type already describes the other person.
    if (!selfIsFirst) return name
    val pair = genderedInverse[inverse]
    return when (genders[rel.member_2]) {
        KnownGender.MALE -> pair?.first ?: inverse
        KnownGender.FEMALE -> pair?.second ?: inverse
        null -> inverse
    }
}

/**
 * (member_1, member_2) to save for a link edited from [selfId]'s page. The type says what member_1
 * IS to member_2, so an edit keeps the stored order: [selfIsFirst] is whether the viewed member was
 * member_1 when the link was opened. A new link always has the viewed member first.
 */
fun relationshipEndpoints(selfId: Int, otherId: Int, selfIsFirst: Boolean): Pair<Int, Int> =
    if (selfIsFirst) selfId to otherId else otherId to selfId

/** "[A] is the [term] of [B]" in stored order, so the sheet reads the same way the link is saved. */
fun relationshipSentence(selfName: String?, otherName: String?, term: String?, selfIsFirst: Boolean): String {
    val self = selfName ?: "..."
    val other = otherName ?: "..."
    val label = term ?: "..."
    return if (selfIsFirst) "$self is the $label of $other" else "$other is the $label of $self"
}
