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
import androidx.compose.foundation.layout.size
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
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Scaffold
import androidx.compose.material3.SnackbarHost
import androidx.compose.material3.SnackbarHostState
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
import com.familytree.familytree.ui.components.BannerAd
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
    var isCreatingTree by remember { mutableStateOf(false) }
    var createTreeError by remember { mutableStateOf("") }
    var joinCode by remember { mutableStateOf("") }
    var joinMessage by remember { mutableStateOf("") }
    var isSubmittingJoin by remember { mutableStateOf(false) }
    var joinError by remember { mutableStateOf("") }
    var loadError by remember { mutableStateOf("") }
    val snackbarHostState = remember { SnackbarHostState() }

    fun loadTrees() {
        scope.launch {
            isLoading = true
            loadError = ""
            val result = repository.getFamilyTrees()
            if (result.isSuccess) {
                trees = result.getOrNull() ?: emptyList()
            } else {
                loadError = result.exceptionOrNull()?.message ?: "Failed to load your trees"
            }
            isLoading = false
        }
    }

    LaunchedEffect(Unit) { loadTrees() }

    Scaffold(
        snackbarHost = { SnackbarHost(snackbarHostState) },
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
        bottomBar = {
            Column {
                BannerAd(modifier = Modifier.fillMaxWidth())
                BottomNavBar(navController = navController, currentRoute = Screen.Home.route)
            }
        }
    ) { padding ->
        if (isLoading) {
            Box(Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
                CircularProgressIndicator(color = Primary)
            }
        } else if (loadError.isNotEmpty()) {
            Box(Modifier.fillMaxSize().padding(padding), contentAlignment = Alignment.Center) {
                Column(horizontalAlignment = Alignment.CenterHorizontally) {
                    Text(loadError, color = TextHint)
                    Spacer(Modifier.height(12.dp))
                    Button(
                        onClick = { loadTrees() },
                        colors = ButtonDefaults.buttonColors(containerColor = Primary)
                    ) { Text("Retry") }
                }
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
                onDismissRequest = { if (!isCreatingTree) { showCreateDialog = false; createTreeError = "" } },
                title = { Text("New Family Tree") },
                text = {
                    Column {
                        OutlinedTextField(
                            value = newTreeName,
                            onValueChange = { newTreeName = it },
                            label = { Text("Tree Name") },
                            modifier = Modifier.fillMaxWidth(),
                            enabled = !isCreatingTree
                        )
                        Spacer(Modifier.height(8.dp))
                        OutlinedTextField(
                            value = newTreeDesc,
                            onValueChange = { newTreeDesc = it },
                            label = { Text("Description (optional)") },
                            modifier = Modifier.fillMaxWidth(),
                            enabled = !isCreatingTree
                        )
                        if (createTreeError.isNotEmpty()) {
                            Spacer(Modifier.height(8.dp))
                            Text(createTreeError, color = MaterialTheme.colorScheme.error, fontSize = 13.sp)
                        }
                    }
                },
                confirmButton = {
                    Button(
                        onClick = {
                            createTreeError = ""
                            isCreatingTree = true
                            scope.launch {
                                val result = repository.createFamilyTree(newTreeName, newTreeDesc)
                                isCreatingTree = false
                                if (result.isSuccess) {
                                    trees = trees + result.getOrNull()!!
                                    showCreateDialog = false
                                    newTreeName = ""
                                    newTreeDesc = ""
                                } else {
                                    createTreeError = result.exceptionOrNull()?.message ?: "Failed to create tree"
                                }
                            }
                        },
                        enabled = !isCreatingTree && newTreeName.isNotBlank()
                    ) {
                        if (isCreatingTree) {
                            CircularProgressIndicator(color = Color.White, modifier = Modifier.size(20.dp))
                        } else {
                            Text("Create")
                        }
                    }
                },
                dismissButton = {
                    TextButton(
                        onClick = { showCreateDialog = false; createTreeError = "" },
                        enabled = !isCreatingTree
                    ) { Text("Cancel") }
                }
            )
        }

        if (showJoinDialog) {
            AlertDialog(
                onDismissRequest = { if (!isSubmittingJoin) { showJoinDialog = false; joinError = "" } },
                title = { Text("Join Family Tree") },
                text = {
                    Column {
                        OutlinedTextField(
                            value = joinCode,
                            onValueChange = { joinCode = it.uppercase() },
                            label = { Text("Family Code") },
                            modifier = Modifier.fillMaxWidth(),
                            enabled = !isSubmittingJoin
                        )
                        Spacer(Modifier.height(8.dp))
                        OutlinedTextField(
                            value = joinMessage,
                            onValueChange = { joinMessage = it },
                            label = { Text("Introduce yourself to the tree owner") },
                            modifier = Modifier.fillMaxWidth(),
                            enabled = !isSubmittingJoin
                        )
                        if (joinError.isNotEmpty()) {
                            Spacer(Modifier.height(8.dp))
                            Text(joinError, color = MaterialTheme.colorScheme.error, fontSize = 13.sp)
                        }
                        if (isSubmittingJoin) {
                            Spacer(Modifier.height(12.dp))
                            Box(Modifier.fillMaxWidth(), contentAlignment = Alignment.Center) {
                                CircularProgressIndicator(color = Primary, modifier = Modifier.size(28.dp))
                            }
                        }
                    }
                },
                confirmButton = {
                    Button(
                        onClick = {
                            joinError = ""
                            isSubmittingJoin = true
                            scope.launch {
                                val result = repository.submitJoinRequest(joinCode, joinMessage)
                                isSubmittingJoin = false
                                if (result.isSuccess) {
                                    val body = result.getOrNull()!!
                                    val message = if (body.auto_approved) {
                                        val refreshed = repository.getFamilyTrees()
                                        if (refreshed.isSuccess) trees = refreshed.getOrNull() ?: emptyList()
                                        body.message
                                    } else {
                                        "Request sent! The tree owner will review your request."
                                    }
                                    showJoinDialog = false
                                    joinCode = ""
                                    joinMessage = ""
                                    snackbarHostState.showSnackbar(message)
                                } else {
                                    joinError = result.exceptionOrNull()?.message ?: "Something went wrong. Please try again."
                                }
                            }
                        },
                        enabled = !isSubmittingJoin && joinCode.isNotBlank()
                    ) { Text("Send Request") }
                },
                dismissButton = {
                    TextButton(
                        onClick = { showJoinDialog = false; joinError = "" },
                        enabled = !isSubmittingJoin
                    ) { Text("Cancel") }
                }
            )
        }
    }
}
