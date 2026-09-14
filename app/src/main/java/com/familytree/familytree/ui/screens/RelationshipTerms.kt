package com.familytree.familytree.ui.screens

// Culture-specific relationship terms shown in the Add Relationship picker. Each term maps
// onto one of the RelationshipType rows Django already seeds (englishType must exactly match
// a `type_name` in that table) - these are just localized aliases/labels for the same
// underlying relationship, not separate backend records.

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

// Shown alongside every non-English language's own terms, so switching languages doesn't lose
// access to the handful of universally-needed relations that language doesn't have a cultural
// word for in this app's data. Kept deliberately small so the selected language's own terms
// visually dominate the list instead of being buried under the full English set.
private val basicEnglishTerms = listOf(
    RelationshipTerm("Father", "Father", RelationshipCategory.PARENTS),
    RelationshipTerm("Mother", "Mother", RelationshipCategory.PARENTS),
    RelationshipTerm("Son", "Son", RelationshipCategory.CHILDREN),
    RelationshipTerm("Daughter", "Daughter", RelationshipCategory.CHILDREN),
    RelationshipTerm("Brother", "Brother", RelationshipCategory.SIBLINGS),
    RelationshipTerm("Sister", "Sister", RelationshipCategory.SIBLINGS),
    RelationshipTerm("Spouse", "Spouse", RelationshipCategory.SPOUSE),
    RelationshipTerm("Husband", "Husband", RelationshipCategory.SPOUSE),
    RelationshipTerm("Wife", "Wife", RelationshipCategory.SPOUSE),
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
    RelationshipTerm("Dada", "Grandfather", RelationshipCategory.GRANDPARENTS),
    RelationshipTerm("Dadi", "Grandmother", RelationshipCategory.GRANDPARENTS),
    RelationshipTerm("Nana", "Grandfather", RelationshipCategory.GRANDPARENTS),
    RelationshipTerm("Nani", "Grandmother", RelationshipCategory.GRANDPARENTS),
    RelationshipTerm("Chacha", "Uncle", RelationshipCategory.EXTENDED),
    RelationshipTerm("Chachi", "Aunt", RelationshipCategory.EXTENDED),
    RelationshipTerm("Tau", "Uncle", RelationshipCategory.EXTENDED),
    RelationshipTerm("Tayi", "Aunt", RelationshipCategory.EXTENDED),
    RelationshipTerm("Bua", "Aunt", RelationshipCategory.EXTENDED),
    RelationshipTerm("Fufad", "Uncle", RelationshipCategory.EXTENDED),
    RelationshipTerm("Mama", "Uncle", RelationshipCategory.EXTENDED),
    RelationshipTerm("Mami", "Aunt", RelationshipCategory.EXTENDED),
    RelationshipTerm("Mausi", "Aunt", RelationshipCategory.EXTENDED),
    RelationshipTerm("Mausa", "Uncle", RelationshipCategory.EXTENDED),
    RelationshipTerm("Bhai", "Brother", RelationshipCategory.SIBLINGS),
    RelationshipTerm("Behen", "Sister", RelationshipCategory.SIBLINGS),
    RelationshipTerm("Bhaiya", "Brother", RelationshipCategory.SIBLINGS),
    RelationshipTerm("Didi", "Sister", RelationshipCategory.SIBLINGS),
    RelationshipTerm("Beta", "Son", RelationshipCategory.CHILDREN),
    RelationshipTerm("Beti", "Daughter", RelationshipCategory.CHILDREN),
    RelationshipTerm("Pota", "Grandson", RelationshipCategory.CHILDREN),
    RelationshipTerm("Poti", "Granddaughter", RelationshipCategory.CHILDREN),
    RelationshipTerm("Nati", "Grandson", RelationshipCategory.CHILDREN),
    RelationshipTerm("Naatin", "Granddaughter", RelationshipCategory.CHILDREN),
    RelationshipTerm("Devar", "Brother-in-Law", RelationshipCategory.IN_LAWS),
    RelationshipTerm("Devrani", "Sister-in-Law", RelationshipCategory.IN_LAWS),
    RelationshipTerm("Jeth", "Brother-in-Law", RelationshipCategory.IN_LAWS),
    RelationshipTerm("Jethani", "Sister-in-Law", RelationshipCategory.IN_LAWS),
    RelationshipTerm("Nanad", "Sister-in-Law", RelationshipCategory.IN_LAWS),
    RelationshipTerm("Nanandoi", "Brother-in-Law", RelationshipCategory.IN_LAWS),
    RelationshipTerm("Sala", "Brother-in-Law", RelationshipCategory.IN_LAWS),
    RelationshipTerm("Sali", "Sister-in-Law", RelationshipCategory.IN_LAWS),
    RelationshipTerm("Sasur", "Father-in-Law", RelationshipCategory.IN_LAWS),
    RelationshipTerm("Saas", "Mother-in-Law", RelationshipCategory.IN_LAWS),
)

private val tamilTerms = listOf(
    RelationshipTerm("Thatha", "Grandfather", RelationshipCategory.GRANDPARENTS),
    RelationshipTerm("Paatti", "Grandmother", RelationshipCategory.GRANDPARENTS),
    RelationshipTerm("Chithappa", "Uncle", RelationshipCategory.EXTENDED),
    RelationshipTerm("Chitti", "Aunt", RelationshipCategory.EXTENDED),
    RelationshipTerm("Periyappa", "Uncle", RelationshipCategory.EXTENDED),
    RelationshipTerm("Periyamma", "Aunt", RelationshipCategory.EXTENDED),
    RelationshipTerm("Athhai", "Aunt", RelationshipCategory.EXTENDED),
    RelationshipTerm("Athimber", "Uncle", RelationshipCategory.EXTENDED),
    RelationshipTerm("Mama (Tamil)", "Uncle", RelationshipCategory.EXTENDED),
    RelationshipTerm("Mami (Tamil)", "Aunt", RelationshipCategory.EXTENDED),
    RelationshipTerm("Maami", "Aunt", RelationshipCategory.EXTENDED),
    RelationshipTerm("Chithi", "Aunt", RelationshipCategory.EXTENDED),
    RelationshipTerm("Anna", "Brother", RelationshipCategory.SIBLINGS),
    RelationshipTerm("Akka", "Sister", RelationshipCategory.SIBLINGS),
    RelationshipTerm("Thambi", "Brother", RelationshipCategory.SIBLINGS),
    RelationshipTerm("Thangai", "Sister", RelationshipCategory.SIBLINGS),
    RelationshipTerm("Magan", "Son", RelationshipCategory.CHILDREN),
    RelationshipTerm("Magal", "Daughter", RelationshipCategory.CHILDREN),
    RelationshipTerm("Peyran", "Grandson", RelationshipCategory.CHILDREN),
    RelationshipTerm("Peyartti", "Granddaughter", RelationshipCategory.CHILDREN),
    RelationshipTerm("Maaman", "Father-in-Law", RelationshipCategory.IN_LAWS),
    RelationshipTerm("Maami (In-law)", "Mother-in-Law", RelationshipCategory.IN_LAWS),
    RelationshipTerm("Anni", "Sister-in-Law", RelationshipCategory.IN_LAWS),
    RelationshipTerm("Machan", "Brother-in-Law", RelationshipCategory.IN_LAWS),
    RelationshipTerm("Macchaali", "Sister-in-Law", RelationshipCategory.IN_LAWS),
    RelationshipTerm("Kozhundhan", "Son-in-Law", RelationshipCategory.IN_LAWS),
    RelationshipTerm("Marumagal", "Daughter-in-Law", RelationshipCategory.IN_LAWS),
)

private val teluguTerms = listOf(
    RelationshipTerm("Tata", "Grandfather", RelationshipCategory.GRANDPARENTS),
    RelationshipTerm("Nanna", "Father", RelationshipCategory.PARENTS),
    RelationshipTerm("Amma", "Mother", RelationshipCategory.PARENTS),
    RelationshipTerm("Babai", "Uncle", RelationshipCategory.EXTENDED),
    RelationshipTerm("Atta", "Mother-in-Law", RelationshipCategory.IN_LAWS),
    RelationshipTerm("Mava", "Father-in-Law", RelationshipCategory.IN_LAWS),
    RelationshipTerm("Vadina", "Sister-in-Law", RelationshipCategory.IN_LAWS),
)

private val malayalamTerms = listOf(
    RelationshipTerm("Appachen", "Grandfather", RelationshipCategory.GRANDPARENTS),
    RelationshipTerm("Ammachi", "Grandmother", RelationshipCategory.GRANDPARENTS),
    RelationshipTerm("Achen", "Father", RelationshipCategory.PARENTS),
    RelationshipTerm("Chechi", "Sister", RelationshipCategory.SIBLINGS),
    RelationshipTerm("Chettan", "Brother", RelationshipCategory.SIBLINGS),
    RelationshipTerm("Ammavan", "Uncle", RelationshipCategory.EXTENDED),
    RelationshipTerm("Ammayi", "Aunt", RelationshipCategory.EXTENDED),
)

private val punjabiTerms = listOf(
    RelationshipTerm("Bapuji", "Father", RelationshipCategory.PARENTS),
    RelationshipTerm("Bebeji", "Mother", RelationshipCategory.PARENTS),
    RelationshipTerm("Dadaji", "Grandfather", RelationshipCategory.GRANDPARENTS),
    RelationshipTerm("Nanaji", "Grandfather", RelationshipCategory.GRANDPARENTS),
    RelationshipTerm("Phuphaji", "Uncle", RelationshipCategory.EXTENDED),
    RelationshipTerm("Mausaji", "Uncle", RelationshipCategory.EXTENDED),
    RelationshipTerm("Bhabi", "Sister-in-Law", RelationshipCategory.IN_LAWS),
    RelationshipTerm("Veera", "Brother", RelationshipCategory.SIBLINGS),
)

/** English shows the full English set. Every other language shows ONLY its own cultural terms,
 *  with the small basicEnglishTerms set appended after (not the full English list) so the
 *  selected language's own words are what the user actually sees, not drowned out by English. */
fun termsForLanguage(language: RelationshipLanguage): List<RelationshipTerm> = when (language) {
    RelationshipLanguage.ENGLISH -> englishTerms
    RelationshipLanguage.HINDI -> hindiTerms + basicEnglishTerms
    RelationshipLanguage.TAMIL -> tamilTerms + basicEnglishTerms
    RelationshipLanguage.TELUGU -> teluguTerms + basicEnglishTerms
    RelationshipLanguage.MALAYALAM -> malayalamTerms + basicEnglishTerms
    RelationshipLanguage.PUNJABI -> punjabiTerms + basicEnglishTerms
}
