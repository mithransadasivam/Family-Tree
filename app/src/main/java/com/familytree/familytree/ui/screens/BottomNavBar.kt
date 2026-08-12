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
    NavigationBar(containerColor = Color.White) {
        NavigationBarItem(
            selected = currentRoute == Screen.Home.route,
            onClick = { navController.navigate(Screen.Home.route) },
            icon = { Text("🏠") },
            label = { Text("Home") },
            colors = NavigationBarItemDefaults.colors(indicatorColor = Primary.copy(alpha = 0.1f))
        )
        NavigationBarItem(
            selected = currentRoute.startsWith("tree"),
            onClick = { navController.navigate(Screen.Home.route) },
            icon = { Text("🌳") },
            label = { Text("Trees") },
            colors = NavigationBarItemDefaults.colors(indicatorColor = Primary.copy(alpha = 0.1f))
        )
        NavigationBarItem(
            selected = currentRoute == Screen.Profile.route,
            onClick = { navController.navigate(Screen.Profile.route) },
            icon = { Text("👤") },
            label = { Text("Profile") },
            colors = NavigationBarItemDefaults.colors(indicatorColor = Primary.copy(alpha = 0.1f))
        )
        NavigationBarItem(
            selected = currentRoute == Screen.Settings.route,
            onClick = { navController.navigate(Screen.Settings.route) },
            icon = { Text("⚙️") },
            label = { Text("Settings") },
            colors = NavigationBarItemDefaults.colors(indicatorColor = Primary.copy(alpha = 0.1f))
        )
    }
}
