package com.familytree.familytree.data.repository

import android.content.Context
import androidx.datastore.preferences.core.edit
import com.familytree.familytree.data.api.ApiService
import com.familytree.familytree.data.api.RetrofitClient
import com.familytree.familytree.data.api.TokenManager
import com.familytree.familytree.data.api.dataStore
import com.familytree.familytree.data.models.*
import com.familytree.familytree.data.session.SessionState
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import retrofit2.Response

class AppRepository(context: Context) {
    // Always hold the application context, never the caller's (often an Activity/Compose)
    // context - this instance is short-lived per screen, but the api/dataStore it wires up
    // must not end up retaining a shorter-lived context past the screen's lifetime.
    private val appContext = context.applicationContext
    private val api = getApi(appContext)

    companion object {
        // Retrofit/OkHttp build their own connection pool and dispatcher thread pool - building
        // a new one on every `AppRepository(context)` (previously created fresh per screen via
        // `remember { AppRepository(context) }`) wasted a full network stack per screen visit.
        // One shared instance for the process lifetime is created here instead.
        @Volatile
        private var apiService: ApiService? = null

        private fun getApi(context: Context): ApiService {
            return apiService ?: synchronized(this) {
                apiService ?: RetrofitClient.create(context.applicationContext).also { apiService = it }
            }
        }

        // Set whenever any call comes back 401 (expired/invalid token) so the navigation layer
        // can react in one place - clear the stale token and drop the user back at Login -
        // instead of every screen having to notice and handle it individually.
        private val _sessionExpired = MutableStateFlow(false)
        val sessionExpired: StateFlow<Boolean> = _sessionExpired.asStateFlow()

        fun clearSessionExpiredFlag() {
            _sessionExpired.value = false
        }
    }

    // Centralizes the isSuccessful/body-null/401 handling that used to be repeated (and
    // sometimes force-unwrapped with `!!`) in every single method below - a 2xx response with a
    // null/empty body no longer crashes with an unhelpful NullPointerException, and a 401 now
    // flips the shared sessionExpired flag exactly once instead of being silently swallowed.
    private suspend fun <T> apiCall(block: suspend () -> Response<T>): Result<T> {
        return try {
            val response = block()
            if (response.isSuccessful) {
                val body = response.body()
                if (body != null) Result.success(body)
                else Result.failure(Exception("Empty response from server"))
            } else {
                if (response.code() == 401) expireSession()
                Result.failure(Exception(backendErrorMessage(response)))
            }
        } catch (e: Exception) {
            Result.failure(e)
        }
    }

    private suspend fun apiCallUnit(block: suspend () -> Response<Unit>): Result<Unit> {
        return try {
            val response = block()
            if (response.isSuccessful) {
                Result.success(Unit)
            } else {
                if (response.code() == 401) expireSession()
                Result.failure(Exception(backendErrorMessage(response)))
            }
        } catch (e: Exception) {
            Result.failure(e)
        }
    }

    // A 401 means the session is over: tell the navigation layer, and forget any staff privileges.
    private fun expireSession() {
        _sessionExpired.value = true
        SessionState.clear()
    }

    suspend fun googleAuth(idToken: String): Result<AuthResponse> {
        val result = apiCall { api.googleAuth(mapOf("id_token" to idToken)) }
        result.getOrNull()?.let {
            saveToken(it.tokens.access)
            SessionState.update(it.user) // the sign-in response already carries is_staff / is_superuser
        }
        return result
    }

    suspend fun saveToken(token: String) {
        appContext.dataStore.edit { prefs ->
            prefs[TokenManager.TOKEN_KEY] = token
        }
    }

    suspend fun clearToken() {
        SessionState.clear()
        appContext.dataStore.edit { prefs ->
            prefs.remove(TokenManager.TOKEN_KEY)
        }
    }

    fun isLoggedIn(): Boolean = TokenManager.getToken(appContext) != null

    // Every read of the account refreshes the staff flags, so a revoked superuser loses the entry
    // the next time anything loads the profile.
    suspend fun getMe(): Result<User> =
        apiCall { api.getMe() }.also { r -> r.getOrNull()?.let { SessionState.update(it) } }

    suspend fun updateMe(updates: Map<String, String>): Result<User> = apiCall { api.updateMe(updates) }

    // Superuser-only, read-only. The server returns 403 to anyone else.
    suspend fun getStaffTrees(query: String, offset: Int, limit: Int): Result<StaffTreeList> =
        apiCall { api.getStaffTrees(query, offset, limit) }

    suspend fun getStaffTree(treeId: Int): Result<StaffTreeDetail> = apiCall { api.getStaffTree(treeId) }

    suspend fun getFamilyTrees(): Result<List<FamilyTree>> = apiCall { api.getFamilyTrees() }

    suspend fun getFamilyTree(treeId: Int): Result<FamilyTree> = apiCall { api.getFamilyTree(treeId) }

    suspend fun createFamilyTree(name: String, description: String): Result<FamilyTree> =
        apiCall { api.createFamilyTree(CreateTreeRequest(name, description)) }

    suspend fun getFamilyMembers(treeId: Int): Result<List<FamilyMember>> = apiCall { api.getFamilyMembers(treeId) }

    suspend fun getFamilyMember(memberId: Int): Result<FamilyMember> = apiCall { api.getFamilyMember(memberId) }

    suspend fun updateFamilyMember(memberId: Int, updates: Map<String, String>): Result<FamilyMember> =
        apiCall { api.updateFamilyMember(memberId, updates) }

    suspend fun createFamilyMember(request: CreateMemberRequest): Result<FamilyMember> =
        apiCall { api.createFamilyMember(request) }

    suspend fun deleteFamilyMember(memberId: Int): Result<Unit> = apiCallUnit { api.deleteFamilyMember(memberId) }

    suspend fun getRelationships(treeId: Int): Result<List<Relationship>> = apiCall { api.getRelationships(treeId) }

    suspend fun createRelationship(request: CreateRelationshipRequest): Result<Relationship> =
        apiCall { api.createRelationship(request) }

    suspend fun updateRelationship(relId: Int, request: UpdateRelationshipRequest): Result<Relationship> =
        apiCall { api.updateRelationship(relId, request) }

    suspend fun deleteRelationship(relId: Int): Result<Unit> = apiCallUnit { api.deleteRelationship(relId) }

    suspend fun getRelationshipTypes(): Result<List<RelationshipType>> = apiCall { api.getRelationshipTypes() }

    suspend fun generateFamilyCode(treeId: Int): Result<FamilyCodeResponse> =
        apiCall { api.generateFamilyCode(FamilyCodeRequest(treeId)) }

    suspend fun redeemFamilyCode(code: String): Result<FamilyTree> = apiCall { api.redeemFamilyCode(RedeemCodeRequest(code)) }

    suspend fun getEditHistory(treeId: Int): Result<List<EditHistory>> = apiCall { api.getEditHistory(treeId) }

    suspend fun updateTreeApprovalRequired(treeId: Int, required: Boolean): Result<FamilyTree> =
        apiCall { api.updateTreeSettings(treeId, UpdateTreeSettingsRequest(required)) }

    suspend fun submitJoinRequest(code: String, message: String): Result<SubmitJoinRequestResponse> =
        apiCall { api.submitJoinRequest(SubmitJoinRequestRequest(code, message)) }

    // The server explains most failures ({"error"}, DRF {"detail"}, or per-field validation
    // messages) - surface that instead of a bare status code (see errorMessageFrom).
    private fun backendErrorMessage(response: Response<*>): String =
        errorMessageFrom(response.errorBody()?.string(), response.code())

    suspend fun getPendingRequests(treeId: Int): Result<List<JoinRequest>> = apiCall { api.getPendingRequests(treeId) }

    suspend fun approveRequest(requestId: Int): Result<JoinRequest> =
        apiCall { api.updateJoinRequestStatus(requestId, UpdateJoinRequestStatusRequest("approved")) }

    suspend fun rejectRequest(requestId: Int): Result<JoinRequest> =
        apiCall { api.updateJoinRequestStatus(requestId, UpdateJoinRequestStatusRequest("rejected")) }

    suspend fun leaveTree(treeId: Int): Result<Unit> = apiCallUnit { api.leaveTree(treeId) }

    suspend fun deleteFamilyTree(treeId: Int): Result<Unit> = apiCallUnit { api.deleteFamilyTree(treeId) }

    suspend fun getMyRequests(): Result<List<JoinRequest>> = apiCall { api.getMyJoinRequests() }
}
