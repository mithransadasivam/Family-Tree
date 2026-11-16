package com.familytree.familytree

import com.familytree.familytree.data.models.Relationship
import com.familytree.familytree.ui.screens.KnownGender
import com.familytree.familytree.ui.screens.ParentLink
import com.familytree.familytree.ui.screens.SiblingParentOffer
import com.familytree.familytree.ui.screens.siblingParentOffer
import org.junit.Assert.assertEquals
import org.junit.Assert.assertNull
import org.junit.Test

class SiblingParentOfferTest {
    // 1 = Dharsan (has parents), 2 = Deepa (new sister), 10 = father, 11 = mother
    private fun rel(m1: Int, type: String, m2: Int) = Relationship(
        id = 0, tree = 1, member_1 = m1, member_2 = m2, relationship_type = 0,
        relationship_type_name = type, created_at = "", updated_at = "",
    )

    private val parents = listOf(rel(10, "Father", 1), rel(11, "Mother", 1))

    @Test fun offersTheExistingMembersParentsToTheNewSibling() {
        val offer = siblingParentOffer("Sister", 2, 1, parents, emptyMap())
        assertEquals(SiblingParentOffer(2, listOf(ParentLink(10, "Father"), ParentLink(11, "Mother"))), offer)
    }

    @Test fun worksWhicheverSideTheNewSiblingIsOn() {
        assertEquals(2, siblingParentOffer("Brother", 1, 2, parents, emptyMap())?.childId)
    }

    @Test fun parentsStoredAsSonOrDaughterNeedAKnownGender() {
        val rels = listOf(rel(1, "Son", 10), rel(1, "Son", 11))
        assertNull(siblingParentOffer("Sister", 2, 1, rels, emptyMap()))
        val offer = siblingParentOffer(
            "Sister", 2, 1, rels, mapOf(10 to KnownGender.MALE, 11 to KnownGender.FEMALE),
        )
        assertEquals(listOf(ParentLink(10, "Father"), ParentLink(11, "Mother")), offer?.links)
    }

    @Test fun nothingToOfferWhenNeitherHasParents() {
        assertNull(siblingParentOffer("Sister", 2, 1, emptyList(), emptyMap()))
    }

    @Test fun nothingToOfferWhenBothAlreadyHaveParents() {
        val both = parents + rel(12, "Father", 2)
        assertNull(siblingParentOffer("Sister", 2, 1, both, emptyMap()))
    }

    @Test fun onlyBirthSiblingTypesTriggerAnOffer() {
        assertNull(siblingParentOffer("Step Sister", 2, 1, parents, emptyMap()))
        assertNull(siblingParentOffer("Cousin", 2, 1, parents, emptyMap()))
    }
}
