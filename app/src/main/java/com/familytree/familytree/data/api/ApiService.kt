package com.familytree.familytree.data.api

import com.familytree.familytree.data.models.*
import retrofit2.Response
import retrofit2.http.*

interface ApiService {

    @POST("auth/google/")
    suspend fun googleAuth(@Body body: Map<String, String>): Response<AuthResponse>

    @GET("users/me/")
    suspend fun getMe(): Response<User>

    @PATCH("users/me/")
    suspend fun updateMe(@Body body: Map<String, String>): Response<User>

    @GET("family-trees/")
    suspend fun getFamilyTrees(): Response<List<FamilyTree>>

    @POST("family-trees/")
    suspend fun createFamilyTree(@Body body: CreateTreeRequest): Response<FamilyTree>

    @GET("family-trees/{id}/")
    suspend fun getFamilyTree(@Path("id") id: Int): Response<FamilyTree>

    @DELETE("family-trees/{id}/")
    suspend fun deleteFamilyTree(@Path("id") id: Int): Response<Unit>

    @GET("family-members/")
    suspend fun getFamilyMembers(@Query("tree_id") treeId: Int): Response<List<FamilyMember>>

    @POST("family-members/")
    suspend fun createFamilyMember(@Body body: CreateMemberRequest): Response<FamilyMember>

    @GET("family-members/{id}/")
    suspend fun getFamilyMember(@Path("id") id: Int): Response<FamilyMember>

    @PATCH("family-members/{id}/")
    suspend fun updateFamilyMember(@Path("id") id: Int, @Body body: Map<String, String>): Response<FamilyMember>

    @DELETE("family-members/{id}/")
    suspend fun deleteFamilyMember(@Path("id") id: Int): Response<Unit>

    @GET("relationships/")
    suspend fun getRelationships(@Query("tree_id") treeId: Int): Response<List<Relationship>>

    @POST("relationships/")
    suspend fun createRelationship(@Body body: CreateRelationshipRequest): Response<Relationship>

    @DELETE("relationships/{id}/")
    suspend fun deleteRelationship(@Path("id") id: Int): Response<Unit>

    @GET("relationship-types/")
    suspend fun getRelationshipTypes(): Response<List<RelationshipType>>

    @POST("family-codes/generate/")
    suspend fun generateFamilyCode(@Body body: FamilyCodeRequest): Response<FamilyCodeResponse>

    @POST("family-codes/redeem/")
    suspend fun redeemFamilyCode(@Body body: RedeemCodeRequest): Response<FamilyTree>

    @GET("edit-history/")
    suspend fun getEditHistory(@Query("tree_id") treeId: Int): Response<List<EditHistory>>
}
