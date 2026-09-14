package com.familytree.familytree.data.api

// Single source of truth for the Google Sign-In web client ID - previously duplicated as an
// identical string literal in both LoginScreen.kt and SettingsScreen.kt, risking the two
// drifting apart if the OAuth client is ever rotated.
object AuthConfig {
    const val GOOGLE_WEB_CLIENT_ID = "274201294258-7sd4aqc4m7vm54avvas15ir20c7aq4gn.apps.googleusercontent.com"
}
