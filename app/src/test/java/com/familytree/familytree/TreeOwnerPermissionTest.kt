package com.familytree.familytree

import com.familytree.familytree.ui.screens.canDeleteInTree
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test
import java.io.File

/**
 * Permission model: every member can add and edit people and relationships, but only the tree
 * owner can delete them. The delete actions must not be shown to anyone else.
 */
class TreeOwnerPermissionTest {
    @Test
    fun onlyTheOwnerCanDelete() {
        assertTrue(canDeleteInTree(meId = 7, ownerId = 7))
        assertFalse(canDeleteInTree(meId = 8, ownerId = 7))
    }

    @Test
    fun unknownMeansHiddenNotShown() {
        // Still loading, or the lookup failed: never show delete actions on a guess.
        assertFalse(canDeleteInTree(meId = null, ownerId = 7))
        assertFalse(canDeleteInTree(meId = 7, ownerId = null))
        assertFalse(canDeleteInTree(meId = null, ownerId = null))
    }

    @Test
    fun everyDeleteIconOnTheMemberScreenIsGatedOnCanDelete() {
        val source = File("src/main/java/com/familytree/familytree/ui/screens/MemberDetailScreen.kt").readText()
        val deleteIcons = Regex("""Icons\.(Filled|Default)\.Delete""").findAll(source).toList()
        assertEquals("expected the member and relationship delete icons", 2, deleteIcons.size)
        for (icon in deleteIcons) {
            val before = source.substring(maxOf(0, icon.range.first - 350), icon.range.first)
            assertTrue("a delete icon is not inside an `if (canDelete)` block:\n$before", "if (canDelete)" in before)
        }
    }
}
