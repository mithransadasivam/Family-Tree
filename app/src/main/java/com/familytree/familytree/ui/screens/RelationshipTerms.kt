package com.familytree.familytree.ui.screens

// Culture-specific relationship terms shown in the Add Relationship picker. Each term maps
// onto one of the RelationshipType rows Django already seeds (englishType must exactly match
// a `type_name` in that table) - these are just localized aliases/labels for the same
// underlying relationship, not separate backend records. Each language's list is shown in
// strict isolation (see termsForLanguage) - no term from one language ever appears while
// another language tab is selected.

enum class RelationshipLanguage(val emoji: String, val label: String) {
    ENGLISH("🌍", "English"),
    HINDI("🇮🇳", "Hindi"),
    TAMIL("🇮🇳", "Tamil"),
    TELUGU("🇮🇳", "Telugu"),
    MALAYALAM("🇲🇾", "Malayalam"),
    PUNJABI("🇮🇳", "Punjabi"),
}

enum class RelationshipCategory(val emoji: String, val label: String) {
    SPOUSE("💍", "Spouse & Partner"),
    GRANDPARENTS("👴", "Grandparents"),
    PARENTS("👨‍👩‍👧", "Parents"),
    SIBLINGS("👫", "Siblings"),
    CHILDREN("👶", "Children & Grandchildren"),
    IN_LAWS("🤝", "In-Laws"),
    EXTENDED("👥", "Extended Family"),
}

data class RelationshipTerm(
    val label: String,
    val englishType: String,
    val category: RelationshipCategory
)

private val englishTerms = listOf(
    RelationshipTerm("Father", "Father", RelationshipCategory.PARENTS),
    RelationshipTerm("Mother", "Mother", RelationshipCategory.PARENTS),
    RelationshipTerm("Son", "Son", RelationshipCategory.CHILDREN),
    RelationshipTerm("Daughter", "Daughter", RelationshipCategory.CHILDREN),
    RelationshipTerm("Brother", "Brother", RelationshipCategory.SIBLINGS),
    RelationshipTerm("Sister", "Sister", RelationshipCategory.SIBLINGS),
    RelationshipTerm("Grandfather", "Grandfather", RelationshipCategory.GRANDPARENTS),
    RelationshipTerm("Grandmother", "Grandmother", RelationshipCategory.GRANDPARENTS),
    RelationshipTerm("Grandson", "Grandson", RelationshipCategory.CHILDREN),
    RelationshipTerm("Granddaughter", "Granddaughter", RelationshipCategory.CHILDREN),
    RelationshipTerm("Uncle", "Uncle", RelationshipCategory.EXTENDED),
    RelationshipTerm("Aunt", "Aunt", RelationshipCategory.EXTENDED),
    RelationshipTerm("Cousin", "Cousin", RelationshipCategory.EXTENDED),
    RelationshipTerm("Spouse", "Spouse", RelationshipCategory.SPOUSE),
    RelationshipTerm("Husband", "Husband", RelationshipCategory.SPOUSE),
    RelationshipTerm("Wife", "Wife", RelationshipCategory.SPOUSE),
    RelationshipTerm("Partner", "Partner", RelationshipCategory.SPOUSE),
    RelationshipTerm("Guardian", "Guardian", RelationshipCategory.EXTENDED),
    RelationshipTerm("Father-in-Law", "Father-in-Law", RelationshipCategory.IN_LAWS),
    RelationshipTerm("Mother-in-Law", "Mother-in-Law", RelationshipCategory.IN_LAWS),
    RelationshipTerm("Son-in-Law", "Son-in-Law", RelationshipCategory.IN_LAWS),
    RelationshipTerm("Daughter-in-Law", "Daughter-in-Law", RelationshipCategory.IN_LAWS),
    RelationshipTerm("Brother-in-Law", "Brother-in-Law", RelationshipCategory.IN_LAWS),
    RelationshipTerm("Sister-in-Law", "Sister-in-Law", RelationshipCategory.IN_LAWS),
    RelationshipTerm("Adopted Son", "Adopted Son", RelationshipCategory.CHILDREN),
    RelationshipTerm("Adopted Daughter", "Adopted Daughter", RelationshipCategory.CHILDREN),
    RelationshipTerm("Step Father", "Step Father", RelationshipCategory.PARENTS),
    RelationshipTerm("Step Mother", "Step Mother", RelationshipCategory.PARENTS),
    RelationshipTerm("Step Son", "Step Son", RelationshipCategory.CHILDREN),
    RelationshipTerm("Step Daughter", "Step Daughter", RelationshipCategory.CHILDREN),
    RelationshipTerm("Step Brother", "Step Brother", RelationshipCategory.SIBLINGS),
    RelationshipTerm("Step Sister", "Step Sister", RelationshipCategory.SIBLINGS),
    RelationshipTerm("Fiance", "Fiance", RelationshipCategory.SPOUSE),
    RelationshipTerm("Fiancee", "Fiancee", RelationshipCategory.SPOUSE),
)

private val hindiTerms = listOf(
    RelationshipTerm("Pita", "Father", RelationshipCategory.PARENTS),
    RelationshipTerm("Papa", "Father", RelationshipCategory.PARENTS),
    RelationshipTerm("Mata", "Mother", RelationshipCategory.PARENTS),
    RelationshipTerm("Maa", "Mother", RelationshipCategory.PARENTS),
    RelationshipTerm("Dada", "Grandfather", RelationshipCategory.GRANDPARENTS),
    RelationshipTerm("Dadi", "Grandmother", RelationshipCategory.GRANDPARENTS),
    RelationshipTerm("Nana", "Grandfather", RelationshipCategory.GRANDPARENTS),
    RelationshipTerm("Nani", "Grandmother", RelationshipCategory.GRANDPARENTS),
    RelationshipTerm("Bade Papa", "Uncle", RelationshipCategory.EXTENDED),
    RelationshipTerm("Badi Maa", "Aunt", RelationshipCategory.EXTENDED),
    RelationshipTerm("Chacha", "Uncle", RelationshipCategory.EXTENDED),
    RelationshipTerm("Chachi", "Aunt", RelationshipCategory.EXTENDED),
    RelationshipTerm("Bua", "Aunt", RelationshipCategory.EXTENDED),
    RelationshipTerm("Phupa", "Uncle", RelationshipCategory.EXTENDED),
    RelationshipTerm("Mama", "Uncle", RelationshipCategory.EXTENDED),
    RelationshipTerm("Mami", "Aunt", RelationshipCategory.EXTENDED),
    RelationshipTerm("Mausi", "Aunt", RelationshipCategory.EXTENDED),
    RelationshipTerm("Mausa", "Uncle", RelationshipCategory.EXTENDED),
    RelationshipTerm("Bhai", "Brother", RelationshipCategory.SIBLINGS),
    RelationshipTerm("Bhaiya", "Brother", RelationshipCategory.SIBLINGS),
    RelationshipTerm("Behen", "Sister", RelationshipCategory.SIBLINGS),
    RelationshipTerm("Didi", "Sister", RelationshipCategory.SIBLINGS),
    RelationshipTerm("Beta", "Son", RelationshipCategory.CHILDREN),
    RelationshipTerm("Beti", "Daughter", RelationshipCategory.CHILDREN),
    RelationshipTerm("Pota", "Grandson", RelationshipCategory.CHILDREN),
    RelationshipTerm("Poti", "Granddaughter", RelationshipCategory.CHILDREN),
    RelationshipTerm("Nati", "Grandson", RelationshipCategory.CHILDREN),
    RelationshipTerm("Naatin", "Granddaughter", RelationshipCategory.CHILDREN),
    RelationshipTerm("Bahu", "Daughter-in-Law", RelationshipCategory.IN_LAWS),
    RelationshipTerm("Damad", "Son-in-Law", RelationshipCategory.IN_LAWS),
    RelationshipTerm("Sasur", "Father-in-Law", RelationshipCategory.IN_LAWS),
    RelationshipTerm("Saas", "Mother-in-Law", RelationshipCategory.IN_LAWS),
    RelationshipTerm("Devar", "Brother-in-Law", RelationshipCategory.IN_LAWS),
    RelationshipTerm("Devrani", "Sister-in-Law", RelationshipCategory.IN_LAWS),
    RelationshipTerm("Jeth", "Brother-in-Law", RelationshipCategory.IN_LAWS),
    RelationshipTerm("Jethani", "Sister-in-Law", RelationshipCategory.IN_LAWS),
    RelationshipTerm("Nanad", "Sister-in-Law", RelationshipCategory.IN_LAWS),
    RelationshipTerm("Sala", "Brother-in-Law", RelationshipCategory.IN_LAWS),
    RelationshipTerm("Sali", "Sister-in-Law", RelationshipCategory.IN_LAWS),
    RelationshipTerm("Pati", "Husband", RelationshipCategory.SPOUSE),
    RelationshipTerm("Patni", "Wife", RelationshipCategory.SPOUSE),
)

private val tamilTerms = listOf(
    RelationshipTerm("Appa", "Father", RelationshipCategory.PARENTS),
    RelationshipTerm("Amma", "Mother", RelationshipCategory.PARENTS),
    RelationshipTerm("Thatha", "Grandfather", RelationshipCategory.GRANDPARENTS),
    // Paati covers both paternal and maternal grandmother - listed once (a duplicate entry
    // would give the LazyColumn two rows with an identical key and crash it).
    RelationshipTerm("Paati", "Grandmother", RelationshipCategory.GRANDPARENTS),
    RelationshipTerm("Thaatha", "Grandfather", RelationshipCategory.GRANDPARENTS),
    RelationshipTerm("Periappa", "Uncle", RelationshipCategory.EXTENDED),
    RelationshipTerm("Periamma", "Aunt", RelationshipCategory.EXTENDED),
    RelationshipTerm("Chithappa", "Uncle", RelationshipCategory.EXTENDED),
    RelationshipTerm("Chithi", "Aunt", RelationshipCategory.EXTENDED),
    RelationshipTerm("Athai", "Aunt", RelationshipCategory.EXTENDED),
    // Athai's husband (father's sister's husband) is also called Mama, same as mother's
    // brother - Dravidian kinship terms don't distinguish the two given cross-cousin marriage
    // customs, so there's no separate "Athimber" entry here.
    RelationshipTerm("Mama", "Uncle", RelationshipCategory.EXTENDED),
    RelationshipTerm("Mami", "Aunt", RelationshipCategory.EXTENDED),
    RelationshipTerm("Akka", "Sister", RelationshipCategory.SIBLINGS),
    RelationshipTerm("Anna", "Brother", RelationshipCategory.SIBLINGS),
    RelationshipTerm("Thambi", "Brother", RelationshipCategory.SIBLINGS),
    RelationshipTerm("Thangai", "Sister", RelationshipCategory.SIBLINGS),
    RelationshipTerm("Magan", "Son", RelationshipCategory.CHILDREN),
    RelationshipTerm("Magal", "Daughter", RelationshipCategory.CHILDREN),
    RelationshipTerm("Paiyan", "Son", RelationshipCategory.CHILDREN),
    RelationshipTerm("Penn", "Daughter", RelationshipCategory.CHILDREN),
    RelationshipTerm("Peyran", "Grandson", RelationshipCategory.CHILDREN),
    RelationshipTerm("Peyartti", "Granddaughter", RelationshipCategory.CHILDREN),
    RelationshipTerm("Marumagal", "Daughter-in-Law", RelationshipCategory.IN_LAWS),
    RelationshipTerm("Marumaghan", "Son-in-Law", RelationshipCategory.IN_LAWS),
    RelationshipTerm("Anni", "Sister-in-Law", RelationshipCategory.IN_LAWS),
    RelationshipTerm("Machan", "Brother-in-Law", RelationshipCategory.IN_LAWS),
    RelationshipTerm("Macha", "Brother-in-Law", RelationshipCategory.IN_LAWS),
    RelationshipTerm("Naathanar", "Father-in-Law", RelationshipCategory.IN_LAWS),
    RelationshipTerm("Manavatti", "Mother-in-Law", RelationshipCategory.IN_LAWS),
    RelationshipTerm("Kandhan", "Husband", RelationshipCategory.SPOUSE),
    RelationshipTerm("Manaivi", "Wife", RelationshipCategory.SPOUSE),
)

private val teluguTerms = listOf(
    RelationshipTerm("Nanna", "Father", RelationshipCategory.PARENTS),
    RelationshipTerm("Amma", "Mother", RelationshipCategory.PARENTS),
    RelationshipTerm("Tata", "Grandfather", RelationshipCategory.GRANDPARENTS),
    RelationshipTerm("Nana", "Grandmother", RelationshipCategory.GRANDPARENTS),
    RelationshipTerm("Pedananna", "Uncle", RelationshipCategory.EXTENDED),
    RelationshipTerm("Pedamma", "Aunt", RelationshipCategory.EXTENDED),
    RelationshipTerm("Babai", "Uncle", RelationshipCategory.EXTENDED),
    RelationshipTerm("Pinni", "Aunt", RelationshipCategory.EXTENDED),
    RelationshipTerm("Mava", "Brother-in-Law", RelationshipCategory.IN_LAWS),
    RelationshipTerm("Vadina", "Sister-in-Law", RelationshipCategory.IN_LAWS),
    RelationshipTerm("Maridi", "Brother-in-Law", RelationshipCategory.IN_LAWS),
    RelationshipTerm("Anni", "Sister-in-Law", RelationshipCategory.IN_LAWS),
    RelationshipTerm("Abbayi", "Son", RelationshipCategory.CHILDREN),
    RelationshipTerm("Ammayi", "Daughter", RelationshipCategory.CHILDREN),
    RelationshipTerm("Alludu", "Son-in-Law", RelationshipCategory.IN_LAWS),
    RelationshipTerm("Kodalu", "Daughter-in-Law", RelationshipCategory.IN_LAWS),
    RelationshipTerm("Bharyaa", "Wife", RelationshipCategory.SPOUSE),
    RelationshipTerm("Bharta", "Husband", RelationshipCategory.SPOUSE),
    RelationshipTerm("Anna", "Brother", RelationshipCategory.SIBLINGS),
    RelationshipTerm("Akka", "Sister", RelationshipCategory.SIBLINGS),
    RelationshipTerm("Thammudu", "Brother", RelationshipCategory.SIBLINGS),
    RelationshipTerm("Chellellu", "Sister", RelationshipCategory.SIBLINGS),
)

private val malayalamTerms = listOf(
    RelationshipTerm("Achan", "Father", RelationshipCategory.PARENTS),
    RelationshipTerm("Amma", "Mother", RelationshipCategory.PARENTS),
    RelationshipTerm("Appooppan", "Grandfather", RelationshipCategory.GRANDPARENTS),
    RelationshipTerm("Ammoomma", "Grandmother", RelationshipCategory.GRANDPARENTS),
    RelationshipTerm("Valiyachan", "Uncle", RelationshipCategory.EXTENDED),
    RelationshipTerm("Valiyamma", "Aunt", RelationshipCategory.EXTENDED),
    RelationshipTerm("Cheriiyachan", "Uncle", RelationshipCategory.EXTENDED),
    RelationshipTerm("Cheriyamma", "Aunt", RelationshipCategory.EXTENDED),
    RelationshipTerm("Ammavan", "Uncle", RelationshipCategory.EXTENDED),
    RelationshipTerm("Ammayi", "Aunt", RelationshipCategory.EXTENDED),
    RelationshipTerm("Chettan", "Brother", RelationshipCategory.SIBLINGS),
    RelationshipTerm("Chechi", "Sister", RelationshipCategory.SIBLINGS),
    RelationshipTerm("Aniyattan", "Brother", RelationshipCategory.SIBLINGS),
    RelationshipTerm("Aniyathi", "Sister", RelationshipCategory.SIBLINGS),
    RelationshipTerm("Makan", "Son", RelationshipCategory.CHILDREN),
    RelationshipTerm("Malakal", "Daughter", RelationshipCategory.CHILDREN),
    RelationshipTerm("Marumon", "Son-in-Law", RelationshipCategory.IN_LAWS),
    RelationshipTerm("Marumakal", "Daughter-in-Law", RelationshipCategory.IN_LAWS),
    RelationshipTerm("Bhartav", "Husband", RelationshipCategory.SPOUSE),
    RelationshipTerm("Bharya", "Wife", RelationshipCategory.SPOUSE),
    RelationshipTerm("Pithavu", "Father-in-Law", RelationshipCategory.IN_LAWS),
    RelationshipTerm("Ammayi (In-law)", "Mother-in-Law", RelationshipCategory.IN_LAWS),
)

private val punjabiTerms = listOf(
    RelationshipTerm("Pita Ji", "Father", RelationshipCategory.PARENTS),
    RelationshipTerm("Papa", "Father", RelationshipCategory.PARENTS),
    RelationshipTerm("Mata Ji", "Mother", RelationshipCategory.PARENTS),
    RelationshipTerm("Maa", "Mother", RelationshipCategory.PARENTS),
    RelationshipTerm("Dada Ji", "Grandfather", RelationshipCategory.GRANDPARENTS),
    RelationshipTerm("Dadi Ji", "Grandmother", RelationshipCategory.GRANDPARENTS),
    RelationshipTerm("Nana Ji", "Grandfather", RelationshipCategory.GRANDPARENTS),
    RelationshipTerm("Nani Ji", "Grandmother", RelationshipCategory.GRANDPARENTS),
    RelationshipTerm("Taya", "Uncle", RelationshipCategory.EXTENDED),
    RelationshipTerm("Tayi", "Aunt", RelationshipCategory.EXTENDED),
    RelationshipTerm("Chacha", "Uncle", RelationshipCategory.EXTENDED),
    RelationshipTerm("Chachi", "Aunt", RelationshipCategory.EXTENDED),
    RelationshipTerm("Bhua", "Aunt", RelationshipCategory.EXTENDED),
    RelationshipTerm("Phufad", "Uncle", RelationshipCategory.EXTENDED),
    RelationshipTerm("Mama", "Uncle", RelationshipCategory.EXTENDED),
    RelationshipTerm("Mami", "Aunt", RelationshipCategory.EXTENDED),
    RelationshipTerm("Maasi", "Aunt", RelationshipCategory.EXTENDED),
    RelationshipTerm("Maasad", "Uncle", RelationshipCategory.EXTENDED),
    RelationshipTerm("Veer", "Brother", RelationshipCategory.SIBLINGS),
    RelationshipTerm("Bhenji", "Sister", RelationshipCategory.SIBLINGS),
    RelationshipTerm("Putt", "Son", RelationshipCategory.CHILDREN),
    RelationshipTerm("Dhee", "Daughter", RelationshipCategory.CHILDREN),
    RelationshipTerm("Pota", "Grandson", RelationshipCategory.CHILDREN),
    RelationshipTerm("Poti", "Granddaughter", RelationshipCategory.CHILDREN),
    RelationshipTerm("Nuh", "Daughter-in-Law", RelationshipCategory.IN_LAWS),
    RelationshipTerm("Jamai", "Son-in-Law", RelationshipCategory.IN_LAWS),
    RelationshipTerm("Sasur", "Father-in-Law", RelationshipCategory.IN_LAWS),
    RelationshipTerm("Saas", "Mother-in-Law", RelationshipCategory.IN_LAWS),
    RelationshipTerm("Devar", "Brother-in-Law", RelationshipCategory.IN_LAWS),
    RelationshipTerm("Jeth", "Brother-in-Law", RelationshipCategory.IN_LAWS),
    RelationshipTerm("Nanad", "Sister-in-Law", RelationshipCategory.IN_LAWS),
    RelationshipTerm("Sala", "Brother-in-Law", RelationshipCategory.IN_LAWS),
    // The source list gave "Sala" for wife's sister too (a duplicate of wife's-brother above) -
    // corrected to "Sali", the standard term, since a duplicate label would crash the
    // LazyColumn (two rows with the same key) and "Sala" specifically means wife's brother.
    RelationshipTerm("Sali", "Sister-in-Law", RelationshipCategory.IN_LAWS),
    RelationshipTerm("Pati", "Husband", RelationshipCategory.SPOUSE),
    RelationshipTerm("Patni", "Wife", RelationshipCategory.SPOUSE),
    RelationshipTerm("Bhabi", "Sister-in-Law", RelationshipCategory.IN_LAWS),
)

/** Strict per-language separation - each language shows ONLY its own terms, never mixed with
 *  any other language (including English). */
fun termsForLanguage(language: RelationshipLanguage): List<RelationshipTerm> = when (language) {
    RelationshipLanguage.ENGLISH -> englishTerms
    RelationshipLanguage.HINDI -> hindiTerms
    RelationshipLanguage.TAMIL -> tamilTerms
    RelationshipLanguage.TELUGU -> teluguTerms
    RelationshipLanguage.MALAYALAM -> malayalamTerms
    RelationshipLanguage.PUNJABI -> punjabiTerms
}

/** Looks up the canonical English term for an existing relationship's stored type name (e.g.
 *  "Grandfather"), used to pre-fill the picker when editing - the backend only ever stores the
 *  canonical English type, not which cultural label was originally chosen, so editing always
 *  re-opens on the English tab regardless of what language the relationship was created in. */
fun findEnglishTerm(englishType: String): RelationshipTerm? = englishTerms.find { it.englishType == englishType }
