package com.familytree.familytree.ui.navigation

import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.remember
import androidx.compose.ui.platform.LocalContext
import androidx.navigation.NavType
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.compose.rememberNavController
import androidx.navigation.navArgument
import com.familytree.familytree.data.repository.AppRepository
import com.familytree.familytree.ui.screens.EditHistoryScreen
import com.familytree.familytree.ui.screens.HomeScreen
import com.familytree.familytree.ui.screens.LoginScreen
import com.familytree.familytree.ui.screens.MemberDetailScreen
import com.familytree.familytree.ui.screens.MyRequestsScreen
import com.familytree.familytree.ui.screens.PendingRequestsScreen
import com.familytree.familytree.ui.screens.ProfileScreen
import com.familytree.familytree.ui.screens.SettingsScreen
import com.familytree.familytree.ui.screens.TreeViewScreen

sealed class Screen(val route: String) {
    object Login : Screen("login")
    object Home : Screen("home")
    object TreeView : Screen("tree/{treeId}") {
        fun createRoute(treeId: Int) = "tree/$treeId"
    }
    object MemberDetail : Screen("member/{memberId}") {
        fun createRoute(memberId: Int) = "member/$memberId"
    }
    object Profile : Screen("profile")
    object Settings : Screen("settings")
    object EditHistory : Screen("history/{treeId}") {
        fun createRoute(treeId: Int) = "history/$treeId"
    }
    object PendingRequests : Screen("pending-requests")
    object MyRequests : Screen("my-requests")
}

@Composable
fun AppNavigation() {
    val navController = rememberNavController()
    val context = LocalContext.current
    val repository = remember { AppRepository(context) }

    // Any API call anywhere in the app that comes back 401 flips this shared flag - react to
    // it in exactly one place instead of every screen having to notice its own requests failing
    // with an expired/invalid token: drop the stale token and send the user back to Login.
    val sessionExpired by AppRepository.sessionExpired.collectAsState()
    LaunchedEffect(sessionExpired) {
        if (sessionExpired) {
            repository.clearToken()
            AppRepository.clearSessionExpiredFlag()
            navController.navigate(Screen.Login.route) {
                popUpTo(navController.graph.id) { inclusive = true }
            }
        }
    }

    NavHost(navController = navController, startDestination = Screen.Login.route) {
        composable(Screen.Login.route) {
            LoginScreen(navController = navController)
        }
        composable(Screen.Home.route) {
            HomeScreen(navController = navController)
        }
        composable(
            Screen.TreeView.route,
            arguments = listOf(navArgument("treeId") { type = NavType.IntType })
        ) { backStackEntry ->
            TreeViewScreen(
                navController = navController,
                treeId = backStackEntry.arguments?.getInt("treeId") ?: 0
            )
        }
        composable(
            Screen.MemberDetail.route,
            arguments = listOf(navArgument("memberId") { type = NavType.IntType })
        ) { backStackEntry ->
            MemberDetailScreen(
                navController = navController,
                memberId = backStackEntry.arguments?.getInt("memberId") ?: 0
            )
        }
        composable(Screen.Profile.route) {
            ProfileScreen(navController = navController)
        }
        composable(Screen.Settings.route) {
            SettingsScreen(navController = navController)
        }
        composable(
            Screen.EditHistory.route,
            arguments = listOf(navArgument("treeId") { type = NavType.IntType })
        ) { backStackEntry ->
            EditHistoryScreen(
                navController = navController,
                treeId = backStackEntry.arguments?.getInt("treeId") ?: 0
            )
        }
        composable(Screen.PendingRequests.route) {
            PendingRequestsScreen(navController = navController)
        }
        composable(Screen.MyRequests.route) {
            MyRequestsScreen(navController = navController)
        }
    }
}
