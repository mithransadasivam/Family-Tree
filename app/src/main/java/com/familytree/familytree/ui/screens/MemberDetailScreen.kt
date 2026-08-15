package com.familytree.familytree.ui.screens

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.heightIn
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
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
                        Card(
                            colors = CardDefaults.cardColors(containerColor = Surface),
                            modifier = Modifier.fillMaxWidth()
                        ) {
                            Row(
                                Modifier.padding(12.dp),
                                verticalAlignment = Alignment.CenterVertically
                            ) {
                                Text("👤", fontSize = 24.sp)
                                Spacer(Modifier.width(12.dp))
                                Column(Modifier.weight(1f)) {
                                    Text(other?.let { "${it.first_name} ${it.last_name}" } ?: "Unknown")
                                    Text(rel.relationship_type_name, color = Primary, fontSize = 11.sp)
                                }
                                IconButton(onClick = {
                                    scope.launch {
                                        repository.deleteRelationship(rel.id)
                                        val relsResult = repository.getRelationships(member!!.tree)
                                        if (relsResult.isSuccess) relationships = relsResult.getOrNull()
                                            ?.filter { it.member_1 == memberId || it.member_2 == memberId }
                                            ?: emptyList()
                                    }
                                }) {
                                    Icon(Icons.Default.Delete, contentDescription = "Delete relationship", tint = Color.Red.copy(alpha = 0.7f))
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

    if (showAddRel && allMembers.isNotEmpty() && relTypes.isNotEmpty()) {
        if (selectedMemberId == 0) selectedMemberId = allMembers.first().id
        if (selectedRelTypeId == 0) selectedRelTypeId = relTypes.first().id

        val selectedOther = allMembers.find { it.id == selectedMemberId }
        val selectedType = relTypes.find { it.id == selectedRelTypeId }

        AlertDialog(
            onDismissRequest = { showAddRel = false },
            title = { Text("Add Relationship") },
            text = {
                Column {
                    // Sentence preview
                    Card(
                        colors = CardDefaults.cardColors(containerColor = Color(0xFFE8F4F1)),
                        modifier = Modifier.fillMaxWidth().padding(bottom = 16.dp)
                    ) {
                        Text(
                            text = "${member?.first_name} is the ${selectedType?.type_name ?: "..."} of ${selectedOther?.first_name ?: "..."}",
                            modifier = Modifier.padding(12.dp),
                            fontSize = 14.sp,
                            color = Color(0xFF2E5C51),
                            fontWeight = FontWeight.Medium
                        )
                    }

                    Text("Select Other Member", fontSize = 12.sp, color = TextHint)
                    Spacer(Modifier.height(4.dp))
                    allMembers.forEach { m ->
                        Row(
                            verticalAlignment = Alignment.CenterVertically,
                            modifier = Modifier.fillMaxWidth()
                        ) {
                            RadioButton(
                                selected = selectedMemberId == m.id,
                                onClick = { selectedMemberId = m.id }
                            )
                            Text("${m.first_name} ${m.last_name}", fontSize = 14.sp)
                        }
                    }

                    Spacer(Modifier.height(12.dp))
                    Text("Relationship Type", fontSize = 12.sp, color = TextHint)
                    Spacer(Modifier.height(4.dp))
                    Box(
                        modifier = Modifier
                            .heightIn(max = 200.dp)
                            .verticalScroll(rememberScrollState())
                    ) {
                        Column {
                            relTypes.forEach { type ->
                                Row(
                                    verticalAlignment = Alignment.CenterVertically,
                                    modifier = Modifier.fillMaxWidth()
                                ) {
                                    RadioButton(
                                        selected = selectedRelTypeId == type.id,
                                        onClick = { selectedRelTypeId = type.id }
                                    )
                                    Column {
                                        Text(type.type_name, fontSize = 14.sp)
                                    }
                                }
                            }
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
                            if (relsResult.isSuccess) relationships = relsResult.getOrNull()
                                ?.filter { it.member_1 == memberId || it.member_2 == memberId }
                                ?: emptyList()
                            showAddRel = false
                        }
                    }
                }) { Text("Add") }
            },
            dismissButton = {
                TextButton(onClick = { showAddRel = false }) { Text("Cancel") }
            }
        )
    }
}
