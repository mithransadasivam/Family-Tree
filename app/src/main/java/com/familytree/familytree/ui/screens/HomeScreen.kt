package com.familytree.familytree.ui.screens

import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Person
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
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
import com.familytree.familytree.data.models.FamilyTree
import com.familytree.familytree.data.repository.AppRepository
import com.familytree.familytree.ui.navigation.Screen
import com.familytree.familytree.ui.theme.Primary
import com.familytree.familytree.ui.theme.Surface
import com.familytree.familytree.ui.theme.TextHint
import com.familytree.familytree.ui.theme.TextPrimary
import kotlinx.coroutines.launch

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun HomeScreen(navController: NavController) {
    val context = LocalContext.current
    val scope = rememberCoroutineScope()
    val repository = remember { AppRepository(context) }
    var trees by remember { mutableStateOf<List<FamilyTree>>(emptyList()) }
    var isLoading by remember { mutableStateOf(true) }
    var showCreateDialog by remember { mutableStateOf(false) }
    var showJoinDialog by remember { mutableStateOf(false) }
    var newTreeName by remember { mutableStateOf("") }
    var newTreeDesc by remember { mutableStateOf("") }
    var joinCode by remember { mutableStateOf("") }

    LaunchedEffect(Unit) {
        val result = repository.getFamilyTrees()
        if (result.isSuccess) trees = result.getOrNull() ?: emptyList()
        isLoading = false
    }

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("My Family Trees", color = Color.White) },
                colors = TopAppBarDefaults.topAppBarColors(containerColor = Primary),
                actions = {
                    IconButton(onClick = { navController.navigate(Screen.Profile.route) }) {
                        Icon(Icons.Filled.Person, contentDescription = "Profile", tint = Color.White)
                    }
                }
            )
        },
        bottomBar = { BottomNavBar(navController = navController, currentRoute = Screen.Home.route) }
    ) { padding ->
        if (isLoading) {
            Box(Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
                CircularProgressIndicator(color = Primary)
            }
        } else {
            LazyColumn(
                modifier = Modifier.fillMaxSize().padding(padding).padding(16.dp),
                verticalArrangement = Arrangement.spacedBy(12.dp)
            ) {
                if (trees.isEmpty()) {
                    item {
                        Box(Modifier.fillMaxWidth().padding(40.dp), contentAlignment = Alignment.Center) {
                            Column(horizontalAlignment = Alignment.CenterHorizontally) {
                                Text("🌳", fontSize = 48.sp)
                                Spacer(Modifier.height(8.dp))
                                Text("No trees yet", color = TextHint)
                                Text("Create or join one to start", color = TextHint, fontSize = 13.sp)
                            }
                        }
                    }
                }
                items(trees) { tree ->
                    Card(
                        modifier = Modifier.fillMaxWidth().clickable {
                            navController.navigate(Screen.TreeView.createRoute(tree.id))
                        },
                        colors = CardDefaults.cardColors(containerColor = Surface)
                    ) {
                        Row(
                            modifier = Modifier.padding(16.dp),
                            verticalAlignment = Alignment.CenterVertically
                        ) {
                            Text("🌳", fontSize = 32.sp)
                            Spacer(Modifier.width(12.dp))
                            Column(Modifier.weight(1f)) {
                                Text(tree.tree_name, fontWeight = FontWeight.Medium, color = TextPrimary)
                                Text("${tree.member_count} members", fontSize = 12.sp, color = TextHint)
                            }
                            Text("›", fontSize = 20.sp, color = Primary)
                        }
                    }
                }
                item {
                    Spacer(Modifier.height(8.dp))
                    Button(
                        onClick = { showCreateDialog = true },
                        modifier = Modifier.fillMaxWidth(),
                        colors = ButtonDefaults.buttonColors(containerColor = Primary)
                    ) { Text("+ Create New Tree") }
                    Spacer(Modifier.height(8.dp))
                    OutlinedButton(
                        onClick = { showJoinDialog = true },
                        modifier = Modifier.fillMaxWidth()
                    ) { Text("+ Join Tree with Code") }
                }
            }
        }

        if (showCreateDialog) {
            AlertDialog(
                onDismissRequest = { showCreateDialog = false },
                title = { Text("New Family Tree") },
                text = {
                    Column {
                        OutlinedTextField(value = newTreeName, onValueChange = { newTreeName = it }, label = { Text("Tree Name") }, modifier = Modifier.fillMaxWidth())
                        Spacer(Modifier.height(8.dp))
                        OutlinedTextField(value = newTreeDesc, onValueChange = { newTreeDesc = it }, label = { Text("Description (optional)") }, modifier = Modifier.fillMaxWidth())
                    }
                },
                confirmButton = {
                    Button(onClick = {
                        scope.launch {
                            val result = repository.createFamilyTree(newTreeName, newTreeDesc)
                            if (result.isSuccess) {
                                trees = trees + result.getOrNull()!!
                                showCreateDialog = false
                                newTreeName = ""
                                newTreeDesc = ""
                            }
                        }
                    }) { Text("Create") }
                },
                dismissButton = { TextButton(onClick = { showCreateDialog = false }) { Text("Cancel") } }
            )
        }

        if (showJoinDialog) {
            AlertDialog(
                onDismissRequest = { showJoinDialog = false },
                title = { Text("Join Family Tree") },
                text = {
                    OutlinedTextField(value = joinCode, onValueChange = { joinCode = it.uppercase() }, label = { Text("Family Code") }, modifier = Modifier.fillMaxWidth())
                },
                confirmButton = {
                    Button(onClick = {
                        scope.launch {
                            val result = repository.redeemFamilyCode(joinCode)
                            if (result.isSuccess) {
                                val refreshed = repository.getFamilyTrees()
                                if (refreshed.isSuccess) trees = refreshed.getOrNull() ?: emptyList()
                                showJoinDialog = false
                                joinCode = ""
                            }
                        }
                    }) { Text("Join") }
                },
                dismissButton = { TextButton(onClick = { showJoinDialog = false }) { Text("Cancel") } }
            )
        }
    }
}
