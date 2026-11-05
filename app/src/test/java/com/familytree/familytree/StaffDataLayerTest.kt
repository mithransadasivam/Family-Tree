package com.familytree.familytree

import com.familytree.familytree.data.api.ApiService
import com.familytree.familytree.data.models.AuthResponse
import com.familytree.familytree.data.models.StaffTreeDetail
import com.familytree.familytree.data.models.StaffTreeList
import com.familytree.familytree.data.models.User
import com.familytree.familytree.data.session.SessionState
import com.google.gson.Gson
import org.junit.After
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNotNull
import org.junit.Assert.assertTrue
import org.junit.Before
import org.junit.Test
import retrofit2.http.DELETE
import retrofit2.http.GET
import retrofit2.http.PATCH
import retrofit2.http.POST
import retrofit2.http.PUT
import java.io.File

class StaffDataLayerTest {
    private val gson = Gson()

    // ---- the payloads the web build already uses (see family_trees/staff.py) --------------------
    private val listJson = """
        {"count": 2, "results": [
          {"id": 1, "tree_name": "Smith Family", "description": "",
           "owner": {"id": 5, "email": "owner@example.com", "first_name": "Olive", "last_name": "Owner",
                     "photo_url": "", "has_avatar": false, "avatar_version": null},
           "is_active": true, "approval_required": true, "account_count": 2, "people_count": 7,
           "created_at": "2026-01-02T03:04:05Z", "updated_at": "2026-01-02T03:04:05Z"},
          {"id": 2, "tree_name": "Jones Family", "description": "x",
           "owner": {"id": 6, "email": "g@example.com", "first_name": "", "last_name": "",
                     "photo_url": "", "has_avatar": false, "avatar_version": null},
           "is_active": false, "approval_required": false, "account_count": 1, "people_count": 0,
           "created_at": "2026-02-03T00:00:00Z", "updated_at": "2026-02-03T00:00:00Z"}]}
    """.trimIndent()

    @Test
    fun staffTreeListParsesIncludingTheDeletedFlag() {
        val list = gson.fromJson(listJson, StaffTreeList::class.java)
        assertEquals(2, list.count)
        val (smith, jones) = list.results
        assertEquals("Smith Family", smith.tree_name)
        assertEquals(7, smith.people_count)
        assertEquals(2, smith.account_count)
        assertTrue(smith.is_active)
        assertFalse(jones.is_active)
        assertEquals("2026-02-03T00:00:00Z", jones.created_at)
    }

    @Test
    fun theOwnerIsTheSlimPublicShapeWithoutPhoneOrAddress() {
        val owner = gson.fromJson(listJson, StaffTreeList::class.java).results[0].owner
        assertEquals("owner@example.com", owner.email)
        assertEquals("Olive Owner", owner.displayName())
        // A blank name falls back to the email, as the web does.
        assertEquals("g@example.com", gson.fromJson(listJson, StaffTreeList::class.java).results[1].owner.displayName())
        // The model has no phone/address to leave null behind: those fields simply do not exist.
        assertTrue(owner.javaClass.declaredFields.none { it.name == "phone" || it.name == "address" })
    }

    @Test
    fun staffTreeDetailParsesMembersAndRelationshipsWithPrivatePhonesBlank() {
        val json = """
            {"tree": ${gson.toJson(gson.fromJson(listJson, StaffTreeList::class.java).results[0])},
             "members": [
               {"id": 1, "tree": 1, "user": null, "first_name": "Ann", "last_name": "T", "gender": "female",
                "phone": "", "phone_public": false, "email": "", "address": "", "photo_url": "",
                "birth_date": "1950-01-01", "birth_place": "", "death_date": null, "death_place": "",
                "created_at": "2026-01-01T00:00:00Z", "updated_at": "2026-01-01T00:00:00Z"},
               {"id": 2, "tree": 1, "user": 9, "first_name": "Ben", "last_name": "T", "gender": "",
                "phone": "555-2222", "phone_public": true, "email": "", "address": "", "photo_url": "",
                "birth_date": null, "birth_place": "", "death_date": null, "death_place": "",
                "created_at": "2026-01-01T00:00:00Z", "updated_at": "2026-01-01T00:00:00Z"}],
             "relationships": [
               {"id": 10, "tree": 1, "member_1": 1, "member_2": 2, "relationship_type": 3,
                "relationship_type_name": "Father", "created_at": "x", "updated_at": "y"}]}
        """.trimIndent()
        val detail = gson.fromJson(json, StaffTreeDetail::class.java)
        assertEquals("Smith Family", detail.tree.tree_name)
        assertEquals(listOf("", "555-2222"), detail.members.map { it.phone })
        assertEquals(9, detail.members[1].user) // linked-account ids parse (H2)
        assertEquals("Father", detail.relationships.single().relationship_type_name)
    }

    // ---- the two staff calls ---------------------------------------------------------------
    @Test
    fun apiHasTheTwoStaffReadCallsAndNothingThatWrites() {
        val staff = ApiService::class.java.methods.filter { m ->
            listOf(GET::class.java, POST::class.java, PUT::class.java, PATCH::class.java, DELETE::class.java)
                .any { a -> m.getAnnotation(a)?.let { ann ->
                    (ann.annotationClass.java.getMethod("value").invoke(ann) as String).startsWith("staff/")
                } == true }
        }
        assertEquals(setOf("getStaffTrees", "getStaffTree"), staff.map { it.name }.toSet())
        assertTrue("staff calls must be GET only", staff.all { it.getAnnotation(GET::class.java) != null })
        val paths = staff.associate { it.name to it.getAnnotation(GET::class.java)!!.value }
        assertEquals("staff/trees/", paths["getStaffTrees"])
        assertEquals("staff/trees/{id}/", paths["getStaffTree"])
    }

    // ---- session flag: who may see the staff entry ------------------------------------------
    @Before @After
    fun resetSession() = SessionState.clear()

    private fun user(staff: Boolean, superuser: Boolean) = gson.fromJson(
        """{"id":1,"email":"a@b.c","first_name":"A","last_name":"B","phone":"","address":"","photo_url":"",
            "created_at":"x","profile":null,"is_staff":$staff,"is_superuser":$superuser}""",
        User::class.java
    )

    @Test
    fun nobodyIsStaffUntilTheServerSaysSo() {
        assertFalse(SessionState.access.value.isSuperuser)
        assertFalse(SessionState.access.value.isStaff)
    }

    @Test
    fun flagsComeFromTheAccountResponse() {
        SessionState.update(user(staff = true, superuser = true))
        assertTrue(SessionState.access.value.isSuperuser)
        assertTrue(SessionState.access.value.isStaff)
    }

    @Test
    fun staffWithoutSuperuserDoesNotGetTheTreeBrowser() {
        SessionState.update(user(staff = true, superuser = false))
        assertTrue(SessionState.access.value.isStaff)
        assertFalse(SessionState.access.value.isSuperuser)
    }

    @Test
    fun anOlderServerResponseWithoutTheFlagsMeansNotSuperuser() {
        val old = gson.fromJson(
            """{"id":1,"email":"a@b.c","first_name":"A","last_name":"B","phone":"","address":"","photo_url":"",
                "created_at":"x","profile":null}""", User::class.java)
        SessionState.update(old)
        assertFalse(SessionState.access.value.isSuperuser)
    }

    @Test
    fun revocationAndLogoutTakeEffect() {
        SessionState.update(user(staff = true, superuser = true))
        SessionState.update(user(staff = false, superuser = false)) // flag removed on the server
        assertFalse(SessionState.access.value.isSuperuser)
        SessionState.update(user(staff = true, superuser = true))
        SessionState.clear() // logout / expired session
        assertFalse(SessionState.access.value.isSuperuser)
        SessionState.update(user(staff = true, superuser = true))
        SessionState.update(null)
        assertFalse(SessionState.access.value.isSuperuser)
    }

    @Test
    fun theLoginResponseCarriesTheFlagsToo() {
        val auth = gson.fromJson(
            """{"user":{"id":1,"email":"a@b.c","first_name":"A","last_name":"B","phone":"","address":"",
                "photo_url":"","created_at":"x","profile":null,"is_staff":true,"is_superuser":true},
                "tokens":{"access":"a","refresh":"r"},"is_new_user":false}""", AuthResponse::class.java)
        assertTrue(auth.user.is_superuser)
    }

    // ---- wiring: the flag is refreshed wherever the account is read, and dropped on sign-out -----
    @Test
    fun repositoryFeedsAndClearsTheSessionState() {
        val src = File("src/main/java/com/familytree/familytree/data/repository/AppRepository.kt").readText()
        fun body(name: String) = src.substringAfter("suspend fun $name").substringBefore("\n    suspend fun ").substringBefore("\n    fun ")
        assertTrue(body("googleAuth").contains("SessionState.update"))
        assertTrue(body("getMe").contains("SessionState.update"))
        assertTrue(body("clearToken").contains("SessionState.clear"))
        // Every 401 handler must go through expireSession(), which flags the expiry AND drops the privileges.
        assertEquals("both apiCall helpers", 2, Regex("""response\.code\(\) == 401\) expireSession\(\)""").findAll(src).count())
        assertFalse("no 401 handler may skip it", src.contains("== 401) _sessionExpired"))
        val expire = src.substringAfter("private fun expireSession()").substringBefore("\n    }")
        assertTrue(expire.contains("_sessionExpired.value = true") && expire.contains("SessionState.clear()"))
        assertNotNull(SessionState.access)
    }
}
