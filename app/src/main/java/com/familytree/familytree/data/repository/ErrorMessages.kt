package com.familytree.familytree.data.repository

import com.google.gson.JsonArray
import com.google.gson.JsonElement
import com.google.gson.JsonObject
import com.google.gson.JsonParser

/**
 * Turns an error response body into something readable. The server reports problems three ways:
 *  - {"error": "..."}          our own views (invalid code, not a member, ...)
 *  - {"detail": "..."}         Django REST framework (403 no permission, 404, ...)
 *  - {"field": ["..."]}        validation errors, one entry per bad field
 * Anything else (empty, HTML, a JSON array) falls back to "Failed: <status>".
 */
fun errorMessageFrom(body: String?, statusCode: Int): String {
    val fallback = "Failed: $statusCode"
    if (body.isNullOrBlank()) return fallback
    val obj: JsonObject = try {
        @Suppress("DEPRECATION")
        JsonParser().parse(body).takeIf { it.isJsonObject }?.asJsonObject ?: return fallback
    } catch (e: Exception) {
        return fallback
    }

    for (key in listOf("error", "detail")) {
        textOf(obj.get(key))?.let { return it }
    }
    for ((field, value) in obj.entrySet()) {
        textOf(value)?.let { return "$field: $it" }
    }
    return fallback
}

/** A string, or the strings of an array joined by spaces; null if there is no usable text. */
private fun textOf(element: JsonElement?): String? {
    if (element == null || element.isJsonNull) return null
    return when {
        element.isJsonPrimitive -> element.asString.trim().takeIf { it.isNotEmpty() }
        element.isJsonArray -> (element as JsonArray)
            .mapNotNull { textOf(it) }
            .joinToString(" ")
            .takeIf { it.isNotEmpty() }
        else -> null
    }
}
