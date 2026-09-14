package com.familytree.familytree.ui.screens

import androidx.compose.material3.NavigationBar
import androidx.compose.material3.NavigationBarItem
import androidx.compose.material3.NavigationBarItemDefaults
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.graphics.Color
import androidx.navigation.NavController
import com.familytree.familytree.ui.navigation.Screen
import com.familytree.familytree.ui.theme.Primary

@Composable
fun BottomNavBar(navController: NavController, currentRoute: String) {
    // Standard single-top bottom-nav navigation: launchSingleTop avoids stacking duplicate
    // copies of the destination, popUpTo(..., saveState = true) clears everything above the
    // popped-to destination while remembering each tab's scroll/state, and restoreState brings
    // that saved state back when returning to a previously-visited tab. Without this,
    // repeatedly switching tabs pushes an ever-growing chain onto the back stack.
    //
    // The graph's real NavHost startDestination is Login, not Home - and Login is removed from
    // the back stack (inclusive popUpTo) the moment sign-in succeeds, so popUpTo(startDestination)
    // would be a no-op for every bottom-nav tap in the app's actual, post-login lifetime. Home is
    // the true root of the tab-switchable area (Login always lands on Home, and every bottom-nav
    // screen is reached from there), so that's the destination to collapse back to.
    fun navigateToTab(route: String) {
        navController.navigate(route) {
            popUpTo(Screen.Home.route) {
                saveState = true
            }
            launchSingleTop = true
            restoreState = true
        }
    }

    NavigationBar(containerColor = Color.White) {
        NavigationBarItem(
            selected = currentRoute == Screen.Home.route,
            onClick = { navigateToTab(Screen.Home.route) },
            icon = { Text("🏠") },
            label = { Text("Home") },
            colors = NavigationBarItemDefaults.colors(indicatorColor = Primary.copy(alpha = 0.1f))
        )
        NavigationBarItem(
            selected = currentRoute.startsWith("tree"),
            onClick = { navigateToTab(Screen.Home.route) },
            icon = { Text("🌳") },
            label = { Text("Trees") },
            colors = NavigationBarItemDefaults.colors(indicatorColor = Primary.copy(alpha = 0.1f))
        )
        NavigationBarItem(
            selected = currentRoute == Screen.Profile.route,
            onClick = { navigateToTab(Screen.Profile.route) },
            icon = { Text("👤") },
            label = { Text("Profile") },
            colors = NavigationBarItemDefaults.colors(indicatorColor = Primary.copy(alpha = 0.1f))
        )
        NavigationBarItem(
            selected = currentRoute == Screen.Settings.route,
            onClick = { navigateToTab(Screen.Settings.route) },
            icon = { Text("⚙️") },
            label = { Text("Settings") },
            colors = NavigationBarItemDefaults.colors(indicatorColor = Primary.copy(alpha = 0.1f))
        )
    }
}
