package com.familytree.familytree.ui.screens

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.ArrowBack
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Switch
import androidx.compose.material3.SwitchDefaults
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
import com.familytree.familytree.data.models.FamilyTree
import com.familytree.familytree.data.models.JoinRequest
import com.familytree.familytree.data.repository.AppRepository
import com.familytree.familytree.ui.theme.Primary
import com.familytree.familytree.ui.theme.PrimaryLight
import com.familytree.familytree.ui.theme.Surface
import com.familytree.familytree.ui.theme.TextHint
import com.familytree.familytree.ui.theme.TextPrimary
import kotlinx.coroutines.launch

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun PendingRequestsScreen(navController: NavController) {
    val context = LocalContext.current
    val scope = rememberCoroutineScope()
    val repository = remember { AppRepository(context) }

    var isLoading by remember { mutableStateOf(true) }
    var ownedTrees by remember { mutableStateOf<List<FamilyTree>>(emptyList()) }
    var requestsByTree by remember { mutableStateOf<Map<Int, List<JoinRequest>>>(emptyMap()) }
    var successMessage by remember { mutableStateOf("") }

    suspend fun loadAll() {
        val meResult = repository.getMe()
        val treesResult = repository.getFamilyTrees()
        val me = meResult.getOrNull()
        if (me != null && treesResult.isSuccess) {
            val owned = treesResult.getOrNull().orEmpty().filter { it.owner.id == me.id }
            ownedTrees = owned
            val map = mutableMapOf<Int, List<JoinRequest>>()
            owned.forEach { tree ->
                map[tree.id] = repository.getPendingRequests(tree.id).getOrNull().orEmpty()
            }
            requestsByTree = map
        }
        isLoading = false
    }

    LaunchedEffect(Unit) { loadAll() }

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("Pending Requests", color = Color.White) },
                navigationIcon = {
                    IconButton(onClick = { navController.popBackStack() }) {
                        Icon(Icons.Filled.ArrowBack, contentDescription = "Back", tint = Color.White)
                    }
                },
                colors = TopAppBarDefaults.topAppBarColors(containerColor = Primary)
            )
        }
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
                if (successMessage.isNotEmpty()) {
                    item {
                        Card(colors = CardDefaults.cardColors(containerColor = Color(0xFFE3F3EC))) {
                            Text(successMessage, color = Color(0xFF2E7D5B), modifier = Modifier.padding(12.dp))
                        }
                    }
                }
                if (ownedTrees.isEmpty()) {
                    item {
                        Box(Modifier.fillMaxWidth().padding(40.dp), contentAlignment = Alignment.Center) {
                            Text("You don't own any trees yet", color = TextHint)
                        }
                    }
                }
                ownedTrees.forEach { tree ->
                    item(key = "header_${tree.id}") {
                        Column {
                            Text(tree.tree_name, fontWeight = FontWeight.Medium, color = TextPrimary, fontSize = 16.sp)
                            Spacer(Modifier.height(4.dp))
                            Row(
                                modifier = Modifier.fillMaxWidth(),
                                horizontalArrangement = Arrangement.SpaceBetween,
                                verticalAlignment = Alignment.CenterVertically
                            ) {
                                Text(
                                    "Require approval for new members",
                                    fontSize = 13.sp,
                                    color = TextHint,
                                    modifier = Modifier.weight(1f)
                                )
                                Switch(
                                    checked = tree.approval_required,
                                    onCheckedChange = { checked ->
                                        scope.launch {
                                            val result = repository.updateTreeApprovalRequired(tree.id, checked)
                                            val updated = result.getOrNull()
                                            if (updated != null) {
                                                ownedTrees = ownedTrees.map { if (it.id == tree.id) updated else it }
                                            }
                                        }
                                    },
                                    colors = SwitchDefaults.colors(checkedThumbColor = Primary, checkedTrackColor = PrimaryLight)
                                )
                            }
                        }
                    }
                    val pending = requestsByTree[tree.id].orEmpty()
                    if (pending.isEmpty()) {
                        item(key = "empty_${tree.id}") {
                            Text("No pending requests", fontSize = 13.sp, color = TextHint)
                        }
                    } else {
                        items(pending, key = { it.id }) { req ->
                            Card(colors = CardDefaults.cardColors(containerColor = Surface)) {
                                Column(Modifier.padding(16.dp)) {
                                    Text(req.requester_name, fontWeight = FontWeight.Medium, color = TextPrimary)
                                    Text(req.requester_email, fontSize = 12.sp, color = TextHint)
                                    if (req.message.isNotBlank()) {
                                        Spacer(Modifier.height(6.dp))
                                        Text("\"${req.message}\"", fontSize = 13.sp, color = TextPrimary)
                                    }
                                    Spacer(Modifier.height(4.dp))
                                    Text(req.created_at.take(10), fontSize = 11.sp, color = TextHint)
                                    Spacer(Modifier.height(10.dp))
                                    Row(horizontalArrangement = Arrangement.spacedBy(10.dp)) {
                                        Button(
                                            onClick = {
                                                scope.launch {
                                                    val result = repository.approveRequest(req.id)
                                                    if (result.isSuccess) {
                                                        requestsByTree = requestsByTree.toMutableMap().apply {
                                                            this[tree.id] = this[tree.id].orEmpty().filter { it.id != req.id }
                                                        }
                                                        successMessage = "Approved ${req.requester_name}'s request"
                                                    }
                                                }
                                            },
                                            colors = ButtonDefaults.buttonColors(containerColor = Color(0xFF3F9142)),
                                            modifier = Modifier.weight(1f)
                                        ) { Text("Approve") }
                                        Button(
                                            onClick = {
                                                scope.launch {
                                                    val result = repository.rejectRequest(req.id)
                                                    if (result.isSuccess) {
                                                        requestsByTree = requestsByTree.toMutableMap().apply {
                                                            this[tree.id] = this[tree.id].orEmpty().filter { it.id != req.id }
                                                        }
                                                    }
                                                }
                                            },
                                            colors = ButtonDefaults.buttonColors(containerColor = Color(0xFFC0392B)),
                                            modifier = Modifier.weight(1f)
                                        ) { Text("Reject") }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }
}
