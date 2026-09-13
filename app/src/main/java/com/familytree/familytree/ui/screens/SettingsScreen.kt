package com.familytree.familytree.ui.screens

import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.Divider
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.material3.TopAppBar
import androidx.compose.material3.TopAppBarDefaults
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.navigation.NavController
import com.familytree.familytree.data.repository.AppRepository
import com.familytree.familytree.ui.navigation.Screen
import com.familytree.familytree.ui.theme.Primary
import com.familytree.familytree.ui.theme.Surface
import com.familytree.familytree.ui.theme.TextHint
import com.familytree.familytree.ui.theme.TextPrimary
import kotlinx.coroutines.launch

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun SettingsScreen(navController: NavController) {
    val context = LocalContext.current
    val scope = rememberCoroutineScope()
    val repository = remember { AppRepository(context) }
    var isTreeOwner by remember { mutableStateOf(false) }
    var pendingCount by remember { mutableStateOf(0) }

    LaunchedEffect(Unit) {
        val me = repository.getMe().getOrNull()
        val treesResult = repository.getFamilyTrees()
        if (me != null && treesResult.isSuccess) {
            val owned = treesResult.getOrNull().orEmpty().filter { it.owner.id == me.id }
            isTreeOwner = owned.isNotEmpty()
            if (isTreeOwner) {
                pendingCount = owned.sumOf { tree ->
                    repository.getPendingRequests(tree.id).getOrNull().orEmpty().size
                }
            }
        }
    }

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("Settings", color = Color.White) },
                colors = TopAppBarDefaults.topAppBarColors(containerColor = Primary)
            )
        },
        bottomBar = { BottomNavBar(navController = navController, currentRoute = Screen.Settings.route) }
    ) { padding ->
        Column(
            modifier = Modifier.fillMaxSize().padding(padding).padding(16.dp)
        ) {
            Text("Account", fontSize = 11.sp, color = TextHint)
            Spacer(Modifier.height(8.dp))
            Card(colors = CardDefaults.cardColors(containerColor = Surface)) {
                Column {
                    SettingsItem("👤", "Edit Profile") { }
                    SettingsItem("🚪", "Log Out", textColor = Color.Red) {
                        scope.launch {
                            repository.clearToken()
                            navController.navigate(Screen.Login.route) {
                                popUpTo(navController.graph.id) {
                                    inclusive = true
                                }
                            }
                        }
                    }
                }
            }
            Spacer(Modifier.height(20.dp))
            Text("Tree Management", fontSize = 11.sp, color = TextHint)
            Spacer(Modifier.height(8.dp))
            Card(colors = CardDefaults.cardColors(containerColor = Surface)) {
                Column {
                    if (isTreeOwner) {
                        SettingsItemWithBadge("📥", "Pending Requests", pendingCount) {
                            navController.navigate(Screen.PendingRequests.route)
                        }
                    }
                    SettingsItem("📤", "My Join Requests") {
                        navController.navigate(Screen.MyRequests.route)
                    }
                }
            }
        }
    }
}

@Composable
fun SettingsItem(icon: String, label: String, textColor: Color = TextPrimary, onClick: () -> Unit) {
    Row(
        modifier = Modifier.fillMaxWidth().clickable { onClick() }.padding(16.dp),
        verticalAlignment = Alignment.CenterVertically
    ) {
        Box(
            modifier = Modifier.size(36.dp),
            contentAlignment = Alignment.Center
        ) { Text(icon, fontSize = 18.sp) }
        Spacer(Modifier.width(12.dp))
        Text(label, color = textColor, modifier = Modifier.weight(1f))
        Text("›", fontSize = 18.sp, color = TextHint)
    }
    Divider(color = Color(0x1A4A7C6F))
}

@Composable
fun SettingsItemWithBadge(icon: String, label: String, badgeCount: Int, onClick: () -> Unit) {
    Row(
        modifier = Modifier.fillMaxWidth().clickable { onClick() }.padding(16.dp),
        verticalAlignment = Alignment.CenterVertically
    ) {
        Box(
            modifier = Modifier.size(36.dp),
            contentAlignment = Alignment.Center
        ) { Text(icon, fontSize = 18.sp) }
        Spacer(Modifier.width(12.dp))
        Text(label, color = TextPrimary, modifier = Modifier.weight(1f))
        if (badgeCount > 0) {
            Box(
                modifier = Modifier
                    .background(Color(0xFFC0392B), CircleShape)
                    .padding(horizontal = 7.dp, vertical = 2.dp)
            ) {
                Text(badgeCount.toString(), color = Color.White, fontSize = 11.sp, fontWeight = FontWeight.Bold)
            }
            Spacer(Modifier.width(8.dp))
        }
        Text("›", fontSize = 18.sp, color = TextHint)
    }
    Divider(color = Color(0x1A4A7C6F))
}
