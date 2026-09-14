package com.familytree.familytree.data.models

data class User(
    val id: Int,
    val email: String,
    val first_name: String,
    val last_name: String,
    val phone: String,
    val address: String,
    val photo_url: String,
    val created_at: String,
    val profile: UserProfile?
)

data class UserProfile(
    val bio: String,
    val location: String,
    val phone: String,
    val email: String,
    val photo_url: String
)

data class FamilyTree(
    val id: Int,
    val tree_name: String,
    val description: String,
    val owner: User,
    val member_count: Int,
    val approval_required: Boolean,
    val created_at: String,
    val updated_at: String
)

data class FamilyMember(
    val id: Int,
    val tree: Int,
    val user: User?,
    val first_name: String,
    val last_name: String,
    val phone: String,
    val email: String,
    val address: String,
    val photo_url: String,
    val birth_date: String?,
    val birth_place: String,
    val death_date: String?,
    val death_place: String,
    val created_at: String,
    val updated_at: String
)

data class RelationshipType(
    val id: Int,
    val type_name: String,
    val category: String,
    val description: String
)

data class Relationship(
    val id: Int,
    val tree: Int,
    val member_1: Int,
    val member_2: Int,
    val relationship_type: Int,
    val relationship_type_name: String,
    val created_at: String,
    val updated_at: String
)

data class AuthResponse(
    val user: User,
    val tokens: Tokens,
    val is_new_user: Boolean
)

data class Tokens(
    val access: String,
    val refresh: String
)

data class CreateTreeRequest(
    val tree_name: String,
    val description: String
)

data class CreateMemberRequest(
    val tree: Int,
    val first_name: String,
    val last_name: String,
    val phone: String,
    val email: String,
    val birth_date: String?,
    val birth_place: String,
    val photo_url: String
)

data class CreateRelationshipRequest(
    val tree: Int,
    val member_1: Int,
    val member_2: Int,
    val relationship_type: Int
)

data class FamilyCodeRequest(
    val tree_id: Int
)

data class RedeemCodeRequest(
    val code: String
)

data class FamilyCodeResponse(
    val code: String,
    val tree: String
)

data class JoinRequest(
    val id: Int,
    val tree: Int,
    val tree_name: String,
    val requester_name: String,
    val requester_email: String,
    val status: String,
    val message: String,
    val created_at: String
)

data class SubmitJoinRequestRequest(
    val code: String,
    val message: String
)

data class SubmitJoinRequestResponse(
    val auto_approved: Boolean,
    val message: String,
    val request: JoinRequest
)

data class UpdateJoinRequestStatusRequest(
    val status: String
)

data class UpdateTreeSettingsRequest(
    val approval_required: Boolean
)

data class EditHistory(
    val id: Int,
    val entity_type: String,
    val entity_id: Int,
    val change_description: String,
    // Nullable: a history row's editing user may since have been removed from the tree, and
    // Gson will silently deserialize a null JSON value here regardless of Kotlin's static
    // nullability, so this must reflect that honestly rather than promising a non-null value.
    val edited_by: User?,
    val edited_at: String
)
