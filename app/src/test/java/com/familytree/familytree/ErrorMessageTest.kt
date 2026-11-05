package com.familytree.familytree

import com.familytree.familytree.data.repository.errorMessageFrom
import org.junit.Assert.assertEquals
import org.junit.Test

/**
 * The server reports problems three ways: {"error": "..."} (our own views), {"detail": "..."}
 * (Django REST framework: 403 "no permission", 404, ...) and {"field": ["..."]} (validation). The app
 * only understood the first, so everything else showed up as a bare "Failed: 400/403".
 */
class ErrorMessageTest {
    @Test
    fun ourOwnErrorKeyIsUsed() {
        assertEquals("Invalid code", errorMessageFrom("""{"error":"Invalid code"}""", 404))
    }

    @Test
    fun drfDetailIsUsed() {
        assertEquals(
            "You do not have permission to perform this action.",
            errorMessageFrom("""{"detail":"You do not have permission to perform this action."}""", 403)
        )
    }

    @Test
    fun fieldValidationErrorsNameTheField() {
        assertEquals(
            "phone: Ensure this field has no more than 20 characters.",
            errorMessageFrom("""{"phone":["Ensure this field has no more than 20 characters."]}""", 400)
        )
    }

    @Test
    fun severalMessagesForOneFieldAreJoined() {
        assertEquals(
            "email: Enter a valid email address. It is too long.",
            errorMessageFrom("""{"email":["Enter a valid email address.","It is too long."]}""", 400)
        )
    }

    @Test
    fun errorWinsOverOtherKeysAndFirstFieldIsUsedOtherwise() {
        assertEquals("Boom", errorMessageFrom("""{"phone":["x"],"error":"Boom"}""", 400))
        assertEquals("first_name: This field is required.",
            errorMessageFrom("""{"first_name":["This field is required."],"phone":["x"]}""", 400))
    }

    @Test
    fun aPlainStringValueIsAccepted() {
        assertEquals("tree: Invalid pk", errorMessageFrom("""{"tree":"Invalid pk"}""", 400))
    }

    @Test
    fun unreadableOrEmptyBodiesFallBackToTheStatusCode() {
        assertEquals("Failed: 500", errorMessageFrom("<html>Server Error</html>", 500))
        assertEquals("Failed: 502", errorMessageFrom("", 502))
        assertEquals("Failed: 400", errorMessageFrom(null, 400))
        assertEquals("Failed: 400", errorMessageFrom("{}", 400))
        assertEquals("Failed: 400", errorMessageFrom("""{"error":""}""", 400))
        assertEquals("Failed: 400", errorMessageFrom("[1,2]", 400))
    }
}
