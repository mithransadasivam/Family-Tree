package com.familytree.familytree

import com.familytree.familytree.data.models.FamilyMember
import com.google.gson.Gson
import com.google.gson.reflect.TypeToken
import org.junit.Assert.assertEquals
import org.junit.Assert.assertNull
import org.junit.Test

/**
 * The API sends `user` as the linked account's id (a number) or null - not a nested object.
 * Declaring it as an object made Gson throw for the WHOLE members list as soon as one person
 * was linked to an account, which the tree screen showed as an empty tree.
 */
class FamilyMemberParsingTest {
    private fun member(id: Int, user: String) = """
        {"id":$id,"tree":1,"user":$user,"first_name":"A$id","last_name":"","gender":"",
         "phone":"","phone_public":false,"email":"","address":"","photo_url":"",
         "birth_date":null,"birth_place":"","death_date":null,"death_place":"",
         "created_at":"2026-01-01T00:00:00Z","updated_at":"2026-01-01T00:00:00Z"}
    """.trimIndent()

    @Test
    fun aMemberLinkedToAnAccountParses() {
        val m = Gson().fromJson(member(1, "42"), FamilyMember::class.java)
        assertEquals(42, m.user)
    }

    @Test
    fun anUnlinkedMemberParses() {
        assertNull(Gson().fromJson(member(1, "null"), FamilyMember::class.java).user)
    }

    @Test
    fun oneLinkedMemberDoesNotBreakTheWholeList() {
        val json = "[${member(1, "null")},${member(2, "7")},${member(3, "null")}]"
        val type = object : TypeToken<List<FamilyMember>>() {}.type
        val list: List<FamilyMember> = Gson().fromJson(json, type)
        assertEquals(listOf(1, 2, 3), list.map { it.id })
        assertEquals(7, list[1].user)
    }
}
