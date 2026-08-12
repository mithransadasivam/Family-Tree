package com.familytree.familytree.data.repository

import android.content.Context
import androidx.datastore.preferences.core.edit
import com.familytree.familytree.data.api.RetrofitClient
import com.familytree.familytree.data.api.TokenManager
import com.familytree.familytree.data.api.dataStore
import com.familytree.familytree.data.models.*

class AppRepository(private val context: Context) {
    private val api = RetrofitClient.create(context)

    suspend fun googleAuth(idToken: String): Result<AuthResponse> {
        return try {
            val response = api.googleAuth(mapOf("id_token" to idToken))
            if (response.isSuccessful && response.body() != null) {
                val auth = response.body()!!
                saveToken(auth.tokens.access)
                Result.success(auth)
            } else {
                Result.failure(Exception("Auth failed: ${response.code()}"))
            }
        } catch (e: Exception) {
            Result.failure(e)
        }
    }

    suspend fun saveToken(token: String) {
        context.dataStore.edit { prefs ->
            prefs[TokenManager.TOKEN_KEY] = token
        }
    }

    suspend fun clearToken() {
        context.dataStore.edit { prefs ->
            prefs.remove(TokenManager.TOKEN_KEY)
        }
    }

    fun isLoggedIn(): Boolean = TokenManager.getToken(context) != null

    suspend fun getMe(): Result<User> {
        return try {
            val response = api.getMe()
            if (response.isSuccessful) Result.success(response.body()!!)
            else Result.failure(Exception("Failed: ${response.code()}"))
        } catch (e: Exception) { Result.failure(e) }
    }

    suspend fun getFamilyTrees(): Result<List<FamilyTree>> {
        return try {
            val response = api.getFamilyTrees()
            if (response.isSuccessful) Result.success(response.body()!!)
            else Result.failure(Exception("Failed: ${response.code()}"))
        } catch (e: Exception) { Result.failure(e) }
    }

    suspend fun createFamilyTree(name: String, description: String): Result<FamilyTree> {
        return try {
            val response = api.createFamilyTree(CreateTreeRequest(name, description))
            if (response.isSuccessful) Result.success(response.body()!!)
            else Result.failure(Exception("Failed: ${response.code()}"))
        } catch (e: Exception) { Result.failure(e) }
    }

    suspend fun getFamilyMembers(treeId: Int): Result<List<FamilyMember>> {
        return try {
            val response = api.getFamilyMembers(treeId)
            if (response.isSuccessful) Result.success(response.body()!!)
            else Result.failure(Exception("Failed: ${response.code()}"))
        } catch (e: Exception) { Result.failure(e) }
    }

    suspend fun getFamilyMember(memberId: Int): Result<FamilyMember> {
        return try {
            val response = api.getFamilyMember(memberId)
            if (response.isSuccessful) Result.success(response.body()!!)
            else Result.failure(Exception("Failed: ${response.code()}"))
        } catch (e: Exception) { Result.failure(e) }
    }

    suspend fun createFamilyMember(request: CreateMemberRequest): Result<FamilyMember> {
        return try {
            val response = api.createFamilyMember(request)
            if (response.isSuccessful) Result.success(response.body()!!)
            else Result.failure(Exception("Failed: ${response.code()}"))
        } catch (e: Exception) { Result.failure(e) }
    }

    suspend fun deleteFamilyMember(memberId: Int): Result<Unit> {
        return try {
            val response = api.deleteFamilyMember(memberId)
            if (response.isSuccessful) Result.success(Unit)
            else Result.failure(Exception("Failed: ${response.code()}"))
        } catch (e: Exception) { Result.failure(e) }
    }

    suspend fun getRelationships(treeId: Int): Result<List<Relationship>> {
        return try {
            val response = api.getRelationships(treeId)
            if (response.isSuccessful) Result.success(response.body()!!)
            else Result.failure(Exception("Failed: ${response.code()}"))
        } catch (e: Exception) { Result.failure(e) }
    }

    suspend fun createRelationship(request: CreateRelationshipRequest): Result<Relationship> {
        return try {
            val response = api.createRelationship(request)
            if (response.isSuccessful) Result.success(response.body()!!)
            else Result.failure(Exception("Failed: ${response.code()}"))
        } catch (e: Exception) { Result.failure(e) }
    }

    suspend fun getRelationshipTypes(): Result<List<RelationshipType>> {
        return try {
            val response = api.getRelationshipTypes()
            if (response.isSuccessful) Result.success(response.body()!!)
            else Result.failure(Exception("Failed: ${response.code()}"))
        } catch (e: Exception) { Result.failure(e) }
    }

    suspend fun generateFamilyCode(treeId: Int): Result<FamilyCodeResponse> {
        return try {
            val response = api.generateFamilyCode(FamilyCodeRequest(treeId))
            if (response.isSuccessful) Result.success(response.body()!!)
            else Result.failure(Exception("Failed: ${response.code()}"))
        } catch (e: Exception) { Result.failure(e) }
    }

    suspend fun redeemFamilyCode(code: String): Result<FamilyTree> {
        return try {
            val response = api.redeemFamilyCode(RedeemCodeRequest(code))
            if (response.isSuccessful) Result.success(response.body()!!)
            else Result.failure(Exception("Failed: ${response.code()}"))
        } catch (e: Exception) { Result.failure(e) }
    }

    suspend fun getEditHistory(treeId: Int): Result<List<EditHistory>> {
        return try {
            val response = api.getEditHistory(treeId)
            if (response.isSuccessful) Result.success(response.body()!!)
            else Result.failure(Exception("Failed: ${response.code()}"))
        } catch (e: Exception) { Result.failure(e) }
    }
}
