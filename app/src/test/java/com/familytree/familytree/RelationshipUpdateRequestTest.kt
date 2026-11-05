package com.familytree.familytree

import com.familytree.familytree.data.api.ApiService
import com.familytree.familytree.data.models.UpdateRelationshipRequest
import com.familytree.familytree.ui.screens.relationshipEndpoints
import com.google.gson.Gson
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test
import retrofit2.http.DELETE
import retrofit2.http.PATCH

/**
 * Editing a relationship used to be "delete it, then create a replacement": when the server
 * rejected the replacement (already connected, would loop, ...) the original was already gone.
 * An edit must be a single in-place PATCH.
 */
class RelationshipUpdateRequestTest {
    @Test
    fun editRequestCarriesOnlyTheEditableFields() {
        val (first, second) = relationshipEndpoints(selfId = 2, otherId = 1, selfIsFirst = false)
        val json = Gson().toJsonTree(UpdateRelationshipRequest(first, second, 7)).asJsonObject
        assertEquals(setOf("member_1", "member_2", "relationship_type"), json.keySet())
        assertEquals(1, json["member_1"].asInt)
        assertEquals(2, json["member_2"].asInt)
        assertEquals(7, json["relationship_type"].asInt)
    }

    @Test
    fun apiHasAnInPlaceUpdateEndpoint() {
        val update = ApiService::class.java.methods.single { it.name == "updateRelationship" }
        assertEquals("relationships/{id}/", update.getAnnotation(PATCH::class.java)?.value)
        assertTrue(update.getAnnotation(DELETE::class.java) == null)
    }

    @Test
    fun editFlowDoesNotDeleteTheRelationshipFirst() {
        // Guard against the old flow coming back: the edit sheet's save handler must not call
        // deleteRelationship before updateRelationship.
        val source = java.io.File("src/main/java/com/familytree/familytree/ui/screens/MemberDetailScreen.kt").readText()
        val save = source.substringAfter("val relIdBeingEdited = editingRelationshipId")
            .substringBefore("enabled = selectedTerm != null")
        assertTrue(save.contains("repository.updateRelationship("))
        assertFalse(save.contains("repository.deleteRelationship("))
    }
}
