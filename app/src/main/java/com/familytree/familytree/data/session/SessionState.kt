package com.familytree.familytree.data.session

import com.familytree.familytree.data.models.User
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow

/** What the signed-in account is allowed to see, as last reported by the server. */
data class StaffAccess(val isStaff: Boolean = false, val isSuperuser: Boolean = false)

/**
 * In-memory only, on purpose. A privilege flag saved to disk could outlive the server revoking it,
 * so it is re-read from /users/me/ (and the sign-in response) every time, and dropped on sign-out
 * or an expired session. It only decides what to SHOW: the server checks every staff request itself.
 * Nobody is staff until the server says so, so a missing flag (older server) means "no".
 */
object SessionState {
    private val _access = MutableStateFlow(StaffAccess())
    val access: StateFlow<StaffAccess> = _access.asStateFlow()

    fun update(user: User?) {
        _access.value = if (user == null) StaffAccess() else StaffAccess(user.is_staff, user.is_superuser)
    }

    fun clear() {
        _access.value = StaffAccess()
    }
}
