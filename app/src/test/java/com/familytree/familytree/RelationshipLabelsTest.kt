package com.familytree.familytree

import com.familytree.familytree.data.models.FamilyMember
import com.familytree.familytree.data.models.Relationship
import com.familytree.familytree.ui.screens.KnownGender
import com.familytree.familytree.ui.screens.inferGenders
import com.familytree.familytree.ui.screens.relationshipLabelFor
import org.junit.Assert.assertEquals
import org.junit.Test

class RelationshipLabelsTest {
    private val a = 1 // member_1: the person the type describes
    private val b = 2 // member_2

    private fun rel(type: String) = Relationship(
        id = 10, tree = 1, member_1 = a, member_2 = b, relationship_type = 0,
        relationship_type_name = type, created_at = "", updated_at = "",
    )

    private fun member(id: Int, gender: String?) = FamilyMember(
        id = id, tree = 1, user = null, first_name = "m$id", last_name = "", phone = "", email = "",
        address = "", photo_url = "", birth_date = null, birth_place = "", death_date = null,
        death_place = "", gender = gender, created_at = "", updated_at = "",
    )

    private val male = mapOf(b to KnownGender.MALE)
    private val female = mapOf(b to KnownGender.FEMALE)

    // type -> (neutral, label if member_2 is male, label if member_2 is female), as seen by member_1
    private val inverses = listOf(
        Triple("Father", "Child", "Son" to "Daughter"),
        Triple("Mother", "Child", "Son" to "Daughter"),
        Triple("Son", "Parent", "Father" to "Mother"),
        Triple("Daughter", "Parent", "Father" to "Mother"),
        Triple("Stepfather", "Stepchild", "Step Son" to "Step Daughter"),
        Triple("Stepmother", "Stepchild", "Step Son" to "Step Daughter"),
        Triple("Step Father", "Stepchild", "Step Son" to "Step Daughter"),
        Triple("Step Mother", "Stepchild", "Step Son" to "Step Daughter"),
        Triple("Stepson", "Step-parent", "Step Father" to "Step Mother"),
        Triple("Stepdaughter", "Step-parent", "Step Father" to "Step Mother"),
        Triple("Step Son", "Step-parent", "Step Father" to "Step Mother"),
        Triple("Step Daughter", "Step-parent", "Step Father" to "Step Mother"),
        Triple("Adopted Son", "Adoptive parent", "Adoptive Father" to "Adoptive Mother"),
        Triple("Adopted Daughter", "Adoptive parent", "Adoptive Father" to "Adoptive Mother"),
        Triple("Grandfather", "Grandchild", "Grandson" to "Granddaughter"),
        Triple("Grandmother", "Grandchild", "Grandson" to "Granddaughter"),
        Triple("Grandson", "Grandparent", "Grandfather" to "Grandmother"),
        Triple("Granddaughter", "Grandparent", "Grandfather" to "Grandmother"),
        Triple("Brother", "Sibling", "Brother" to "Sister"),
        Triple("Sister", "Sibling", "Brother" to "Sister"),
        Triple("Step Brother", "Step-sibling", "Step Brother" to "Step Sister"),
        Triple("Step Sister", "Step-sibling", "Step Brother" to "Step Sister"),
        Triple("Adopted Brother", "Adopted sibling", "Adopted Brother" to "Adopted Sister"),
        Triple("Adopted Sister", "Adopted sibling", "Adopted Brother" to "Adopted Sister"),
        Triple("Husband", "Husband / wife", "Husband" to "Wife"),
        Triple("Wife", "Husband / wife", "Husband" to "Wife"),
        Triple("Fiance", "Fiance / fiancee", "Fiance" to "Fiancee"),
        Triple("Fiancee", "Fiance / fiancee", "Fiance" to "Fiancee"),
        Triple("Father-in-Law", "Child-in-law", "Son-in-Law" to "Daughter-in-Law"),
        Triple("Mother-in-Law", "Child-in-law", "Son-in-Law" to "Daughter-in-Law"),
        Triple("Son-in-Law", "Parent-in-law", "Father-in-Law" to "Mother-in-Law"),
        Triple("Daughter-in-Law", "Parent-in-law", "Father-in-Law" to "Mother-in-Law"),
        Triple("Brother-in-Law", "Sibling-in-law", "Brother-in-Law" to "Sister-in-Law"),
        Triple("Sister-in-Law", "Sibling-in-law", "Brother-in-Law" to "Sister-in-Law"),
        Triple("Uncle", "Nephew / niece", "Nephew" to "Niece"),
        Triple("Aunt", "Nephew / niece", "Nephew" to "Niece"),
    )

    // Types with no gendered inverse: member_1 sees the same word whatever member_2's gender.
    private val ungendered = listOf(
        "Spouse" to "Spouse",
        "Partner" to "Partner",
        "Cousin" to "Cousin",
        "Guardian" to "Ward",
    )

    @Test
    fun member2SeesTheStoredType() {
        (inverses.map { it.first } + ungendered.map { it.first }).forEach { type ->
            assertEquals(type, relationshipLabelFor(rel(type), b, male))
            assertEquals(type, relationshipLabelFor(rel(type), b, female))
        }
    }

    @Test
    fun member1SeesTheNeutralInverseWhenGenderUnknown() {
        inverses.forEach { (type, neutral, _) ->
            assertEquals(type, neutral, relationshipLabelFor(rel(type), a, emptyMap()))
        }
    }

    @Test
    fun member1SeesTheGenderedInverse() {
        inverses.forEach { (type, _, terms) ->
            assertEquals(type, terms.first, relationshipLabelFor(rel(type), a, male))
            assertEquals(type, terms.second, relationshipLabelFor(rel(type), a, female))
        }
    }

    @Test
    fun ungenderedTypesIgnoreGender() {
        ungendered.forEach { (type, expected) ->
            assertEquals(type, expected, relationshipLabelFor(rel(type), a, emptyMap()))
            assertEquals(type, expected, relationshipLabelFor(rel(type), a, male))
            assertEquals(type, expected, relationshipLabelFor(rel(type), a, female))
        }
    }

    @Test
    fun fatherOfIsNotMirrored() {
        // A is the Father of B: B's page says Father, A's page says Son/Daughter.
        assertEquals("Father", relationshipLabelFor(rel("Father"), b, male))
        assertEquals("Son", relationshipLabelFor(rel("Father"), a, male))
        assertEquals("Daughter", relationshipLabelFor(rel("Father"), a, female))
    }

    @Test
    fun unknownTypeFallsBackToStoredName() {
        assertEquals("Godfather of", relationshipLabelFor(rel("Godfather"), a))
        assertEquals("Godfather", relationshipLabelFor(rel("Godfather"), b))
    }

    @Test
    fun gendersAreInferredFromTypesAndRecordedGenderWins() {
        val rels = listOf(rel("Father"), rel("Wife").copy(member_1 = b, member_2 = 3))
        assertEquals(mapOf(a to KnownGender.MALE, b to KnownGender.FEMALE), inferGenders(rels))

        // A recorded gender overrides what the link implied; "other" clears it.
        val recorded = inferGenders(rels, listOf(member(a, "female"), member(b, "other")))
        assertEquals(mapOf(a to KnownGender.FEMALE), recorded)

        // Blank or missing gender leaves the inference alone.
        assertEquals(KnownGender.MALE, inferGenders(rels, listOf(member(a, ""), member(3, null)))[a])
    }
}
