package com.familytree.familytree

import com.familytree.familytree.data.models.Relationship
import com.familytree.familytree.ui.screens.KnownGender
import com.familytree.familytree.ui.screens.relationshipEndpoints
import com.familytree.familytree.ui.screens.relationshipLabelFor
import com.familytree.familytree.ui.screens.relationshipSentence
import org.junit.Assert.assertEquals
import org.junit.Assert.assertNotEquals
import org.junit.Test

class RelationshipEditDirectionTest {
    private val parent = 1
    private val child = 2

    // Stored as "parent IS the Father OF child".
    private val stored = Relationship(
        id = 10, tree = 1, member_1 = parent, member_2 = child, relationship_type = 0,
        relationship_type_name = "Father", created_at = "", updated_at = "",
    )

    // What the edit sheet does: remember which side the viewer is on when it opens, then save.
    private fun saveEdit(rel: Relationship, viewerId: Int, otherId: Int): Pair<Int, Int> =
        relationshipEndpoints(viewerId, otherId, selfIsFirst = rel.member_1 == viewerId)

    @Test
    fun editingFromTheFirstMembersPageKeepsTheOrder() {
        assertEquals(parent to child, saveEdit(stored, viewerId = parent, otherId = child))
    }

    @Test
    fun editingFromTheOtherMembersPageDoesNotFlipTheDirection() {
        val saved = saveEdit(stored, viewerId = child, otherId = parent)
        assertEquals(stored.member_1 to stored.member_2, saved)
        // The old behaviour always put the viewer first, which would have made the child the Father.
        assertNotEquals(child to parent, saved)
    }

    @Test
    fun labelsAreUnchangedFromBothSidesAfterAnEditFromEitherSide() {
        val genders = mapOf(parent to KnownGender.MALE, child to KnownGender.FEMALE)
        for (viewer in listOf(parent, child)) {
            val other = if (viewer == parent) child else parent
            val (m1, m2) = saveEdit(stored, viewer, other)
            val resaved = stored.copy(member_1 = m1, member_2 = m2)
            assertEquals("Father", relationshipLabelFor(resaved, child, genders))
            assertEquals("Daughter", relationshipLabelFor(resaved, parent, genders))
        }
    }

    @Test
    fun newLinksAlwaysPutTheViewedMemberFirst() {
        assertEquals(child to parent, relationshipEndpoints(child, parent, selfIsFirst = true))
    }

    @Test
    fun sheetSentenceMatchesTheStoredOrder() {
        assertEquals("Ann is the Father of Ben", relationshipSentence("Ann", "Ben", "Father", selfIsFirst = true))
        // Viewing Ben (member_2): the sheet must still read "Ann is the Father of Ben".
        assertEquals("Ann is the Father of Ben", relationshipSentence("Ben", "Ann", "Father", selfIsFirst = false))
        assertEquals("... is the ... of ...", relationshipSentence(null, null, null, selfIsFirst = true))
    }
}
