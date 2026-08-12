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
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.ArrowBack
import androidx.compose.material.icons.filled.Delete
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.Divider
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.RadioButton
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
import com.familytree.familytree.data.models.CreateRelationshipRequest
import com.familytree.familytree.data.models.FamilyMember
import com.familytree.familytree.data.models.Relationship
import com.familytree.familytree.data.models.RelationshipType
import com.familytree.familytree.data.repository.AppRepository
import com.familytree.familytree.ui.theme.Primary
import com.familytree.familytree.ui.theme.Surface
import com.familytree.familytree.ui.theme.TextHint
import kotlinx.coroutines.launch

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun MemberDetailScreen(navController: NavController, memberId: Int) {
    val context = LocalContext.current
    val scope = rememberCoroutineScope()
    val repository = remember { AppRepository(context) }
    var member by remember { mutableStateOf<FamilyMember?>(null) }
    var relationships by remember { mutableStateOf<List<Relationship>>(emptyList()) }
    var relTypes by remember { mutableStateOf<List<RelationshipType>>(emptyList()) }
    var allMembers by remember { mutableStateOf<List<FamilyMember>>(emptyList()) }
    var isLoading by remember { mutableStateOf(true) }
    var showAddRel by remember { mutableStateOf(false) }
    var selectedMemberId by remember { mutableStateOf(0) }
    var selectedRelTypeId by remember { mutableStateOf(0) }

    LaunchedEffect(memberId) {
        val memberResult = repository.getFamilyMember(memberId)
        if (memberResult.isSuccess) {
            member = memberResult.getOrNull()
            member?.let { m ->
                val relsResult = repository.getRelationships(m.tree)
                if (relsResult.isSuccess) relationships = relsResult.getOrNull()?.filter { it.member_1 == memberId || it.member_2 == memberId } ?: emptyList()
                val membersResult = repository.getFamilyMembers(m.tree)
                if (membersResult.isSuccess) allMembers = membersResult.getOrNull()?.filter { it.id != memberId } ?: emptyList()
            }
        }
        val typesResult = repository.getRelationshipTypes()
        if (typesResult.isSuccess) relTypes = typesResult.getOrNull() ?: emptyList()
        isLoading = false
    }

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text(member?.first_name ?: "Member", color = Color.White) },
                navigationIcon = {
                    IconButton(onClick = { navController.popBackStack() }) {
                        Icon(Icons.Filled.ArrowBack, contentDescription = "Back", tint = Color.White)
                    }
                },
                actions = {
                    IconButton(onClick = {
                        scope.launch {
                            member?.let { m ->
                                repository.deleteFamilyMember(m.id)
                                navController.popBackStack()
                            }
                        }
                    }) {
                        Icon(Icons.Filled.Delete, contentDescription = "Delete", tint = Color.White)
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
            member?.let { m ->
                LazyColumn(
                    modifier = Modifier.fillMaxSize().padding(padding).padding(16.dp),
                    verticalArrangement = Arrangement.spacedBy(12.dp)
                ) {
                    item {
                        Box(Modifier.fillMaxWidth(), contentAlignment = Alignment.Center) {
                            Column(horizontalAlignment = Alignment.CenterHorizontally) {
                                Text("👤", fontSize = 48.sp)
                                Text("${m.first_name} ${m.last_name}", fontSize = 20.sp, fontWeight = FontWeight.Medium)
                                Text("Member", color = Primary, fontSize = 12.sp)
                            }
                        }
                    }
                    item {
                        Card(colors = CardDefaults.cardColors(containerColor = Surface)) {
                            Column(Modifier.padding(16.dp)) {
                                if (m.phone.isNotEmpty()) {
                                    Row(Modifier.padding(vertical = 8.dp)) {
                                        Text("📱 ", fontSize = 16.sp)
                                        Column {
                                            Text("Phone", fontSize = 11.sp, color = TextHint)
                                            Text(m.phone)
                                        }
                                    }
                                }
                                if (m.birth_date != null) {
                                    Row(Modifier.padding(vertical = 8.dp)) {
                                        Text("🗓 ", fontSize = 16.sp)
                                        Column {
                                            Text("Birth Date", fontSize = 11.sp, color = TextHint)
                                            Text(m.birth_date)
                                        }
                                    }
                                }
                                if (m.birth_place.isNotEmpty()) {
                                    Row(Modifier.padding(vertical = 8.dp)) {
                                        Text("📍 ", fontSize = 16.sp)
                                        Column {
                                            Text("Birth Place", fontSize = 11.sp, color = TextHint)
                                            Text(m.birth_place)
                                        }
                                    }
                                }
                            }
                        }
                    }
                    item {
                        Text("Relationships", fontSize = 11.sp, color = TextHint)
                    }
                    if (relationships.isEmpty()) {
                        item { Text("No relationships yet", color = TextHint, fontSize = 13.sp) }
                    }
                    items(relationships) { rel ->
                        val otherId = if (rel.member_1 == memberId) rel.member_2 else rel.member_1
                        val other = allMembers.find { it.id == otherId }
                        Card(colors = CardDefaults.cardColors(containerColor = Surface)) {
                            Row(Modifier.padding(12.dp), verticalAlignment = Alignment.CenterVertically) {
                                Text("👤", fontSize = 24.sp)
                                Spacer(Modifier.width(12.dp))
                                Column {
                                    Text(other?.let { "${it.first_name} ${it.last_name}" } ?: "Unknown")
                                    Text(rel.relationship_type_name, color = Primary, fontSize = 11.sp)
                                }
                            }
                        }
                    }
                    item {
                        OutlinedButton(
                            onClick = { showAddRel = true },
                            modifier = Modifier.fillMaxWidth()
                        ) { Text("+ Add Relationship") }
                    }
                }
            }
        }
    }

    LaunchedEffect(showAddRel, allMembers, relTypes) {
        if (showAddRel && allMembers.isNotEmpty()) {
            if (selectedMemberId == 0 || allMembers.none { it.id == selectedMemberId }) {
                selectedMemberId = allMembers.first().id
            }
        }
        if (showAddRel && relTypes.isNotEmpty()) {
            if (selectedRelTypeId == 0 || relTypes.none { it.id == selectedRelTypeId }) {
                selectedRelTypeId = relTypes.first().id
            }
        }
    }

    if (showAddRel && allMembers.isNotEmpty() && relTypes.isNotEmpty()) {
        AlertDialog(
            onDismissRequest = { showAddRel = false },
            title = { Text("Add Relationship") },
            text = {
                Column {
                    Text("Select Member", fontSize = 12.sp, color = TextHint)
                    allMembers.forEach { m ->
                        Row(verticalAlignment = Alignment.CenterVertically) {
                            RadioButton(selected = selectedMemberId == m.id, onClick = { selectedMemberId = m.id })
                            Text("${m.first_name} ${m.last_name}")
                        }
                    }
                    Spacer(Modifier.height(8.dp))
                    Text("Relationship Type", fontSize = 12.sp, color = TextHint)
                    relTypes.take(8).forEach { type ->
                        Row(verticalAlignment = Alignment.CenterVertically) {
                            RadioButton(selected = selectedRelTypeId == type.id, onClick = { selectedRelTypeId = type.id })
                            Text(type.type_name)
                        }
                    }
                }
            },
            confirmButton = {
                Button(onClick = {
                    scope.launch {
                        member?.let { m ->
                            repository.createRelationship(
                                CreateRelationshipRequest(
                                    tree = m.tree,
                                    member_1 = m.id,
                                    member_2 = selectedMemberId,
                                    relationship_type = selectedRelTypeId
                                )
                            )
                            val relsResult = repository.getRelationships(m.tree)
                            if (relsResult.isSuccess) relationships = relsResult.getOrNull()?.filter { it.member_1 == memberId || it.member_2 == memberId } ?: emptyList()
                            showAddRel = false
                        }
                    }
                }) { Text("Add") }
            },
            dismissButton = { TextButton(onClick = { showAddRel = false }) { Text("Cancel") } }
        )
    }
}
