package com.familytree.familytree.ui.screens

import androidx.compose.foundation.Canvas
import androidx.compose.foundation.gestures.detectTapGestures
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.ArrowBack
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
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
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.graphics.nativeCanvas
import androidx.compose.ui.input.pointer.pointerInput
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.unit.dp
import androidx.navigation.NavController
import com.familytree.familytree.data.models.CreateMemberRequest
import com.familytree.familytree.data.models.FamilyMember
import com.familytree.familytree.data.models.Relationship
import com.familytree.familytree.data.repository.AppRepository
import com.familytree.familytree.ui.navigation.Screen
import com.familytree.familytree.ui.theme.Primary
import com.familytree.familytree.ui.theme.TextHint
import kotlinx.coroutines.launch
import kotlin.math.ceil
import kotlin.math.sqrt

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun TreeViewScreen(navController: NavController, treeId: Int) {
    val context = LocalContext.current
    val scope = rememberCoroutineScope()
    val repository = remember { AppRepository(context) }
    var members by remember { mutableStateOf<List<FamilyMember>>(emptyList()) }
    var relationships by remember { mutableStateOf<List<Relationship>>(emptyList()) }
    var isLoading by remember { mutableStateOf(true) }
    var showAddMember by remember { mutableStateOf(false) }
    var newFirstName by remember { mutableStateOf("") }
    var newLastName by remember { mutableStateOf("") }
    var newPhone by remember { mutableStateOf("") }
    var newBirthPlace by remember { mutableStateOf("") }

    fun loadData() {
        scope.launch {
            val membersResult = repository.getFamilyMembers(treeId)
            val relsResult = repository.getRelationships(treeId)
            if (membersResult.isSuccess) members = membersResult.getOrNull() ?: emptyList()
            if (relsResult.isSuccess) relationships = relsResult.getOrNull() ?: emptyList()
            isLoading = false
        }
    }

    LaunchedEffect(treeId) { loadData() }

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("Family Tree", color = Color.White) },
                navigationIcon = {
                    IconButton(onClick = { navController.popBackStack() }) {
                        Icon(Icons.Filled.ArrowBack, contentDescription = "Back", tint = Color.White)
                    }
                },
                actions = {
                    IconButton(onClick = { showAddMember = true }) {
                        Text("+", color = Color.White, style = MaterialTheme.typography.titleLarge)
                    }
                },
                colors = TopAppBarDefaults.topAppBarColors(containerColor = Primary)
            )
        },
        bottomBar = { BottomNavBar(navController = navController, currentRoute = "tree/$treeId") }
    ) { padding ->
        Box(modifier = Modifier.fillMaxSize().padding(padding)) {
            if (isLoading) {
                CircularProgressIndicator(modifier = Modifier.align(Alignment.Center), color = Primary)
            } else if (members.isEmpty()) {
                Column(
                    modifier = Modifier.align(Alignment.Center),
                    horizontalAlignment = Alignment.CenterHorizontally
                ) {
                    Text("🌳", style = MaterialTheme.typography.displayLarge)
                    Text("Add family members to see the tree", color = TextHint)
                    Spacer(Modifier.height(16.dp))
                    Button(
                        onClick = { showAddMember = true },
                        colors = ButtonDefaults.buttonColors(containerColor = Primary)
                    ) { Text("+ Add Family Member") }
                }
            } else {
                FamilyTreeCanvas(
                    members = members,
                    relationships = relationships,
                    onMemberClick = { member ->
                        navController.navigate(Screen.MemberDetail.createRoute(member.id))
                    }
                )
                Button(
                    onClick = { showAddMember = true },
                    modifier = Modifier.align(Alignment.BottomCenter).fillMaxWidth().padding(16.dp),
                    colors = ButtonDefaults.buttonColors(containerColor = Primary)
                ) { Text("+ Add Family Member") }
            }
        }
    }

    if (showAddMember) {
        AlertDialog(
            onDismissRequest = { showAddMember = false },
            title = { Text("Add Family Member") },
            text = {
                Column {
                    OutlinedTextField(value = newFirstName, onValueChange = { newFirstName = it }, label = { Text("First Name *") }, modifier = Modifier.fillMaxWidth())
                    Spacer(Modifier.height(8.dp))
                    OutlinedTextField(value = newLastName, onValueChange = { newLastName = it }, label = { Text("Last Name") }, modifier = Modifier.fillMaxWidth())
                    Spacer(Modifier.height(8.dp))
                    OutlinedTextField(value = newPhone, onValueChange = { newPhone = it }, label = { Text("Phone") }, modifier = Modifier.fillMaxWidth())
                    Spacer(Modifier.height(8.dp))
                    OutlinedTextField(value = newBirthPlace, onValueChange = { newBirthPlace = it }, label = { Text("Birth Place") }, modifier = Modifier.fillMaxWidth())
                }
            },
            confirmButton = {
                Button(onClick = {
                    if (newFirstName.isNotBlank()) {
                        scope.launch {
                            val result = repository.createFamilyMember(
                                CreateMemberRequest(
                                    tree = treeId,
                                    first_name = newFirstName,
                                    last_name = newLastName,
                                    phone = newPhone,
                                    email = "",
                                    birth_date = null,
                                    birth_place = newBirthPlace,
                                    photo_url = ""
                                )
                            )
                            if (result.isSuccess) {
                                loadData()
                                showAddMember = false
                                newFirstName = ""
                                newLastName = ""
                                newPhone = ""
                                newBirthPlace = ""
                            }
                        }
                    }
                }) { Text("Add") }
            },
            dismissButton = { TextButton(onClick = { showAddMember = false }) { Text("Cancel") } }
        )
    }
}

@Composable
fun FamilyTreeCanvas(
    members: List<FamilyMember>,
    relationships: List<Relationship>,
    onMemberClick: (FamilyMember) -> Unit
) {
    val nodeRadius = 60f
    val positions = remember(members) {
        val map = mutableMapOf<Int, Offset>()
        val cols = maxOf(1, ceil(sqrt(members.size.toDouble())).toInt())
        members.forEachIndexed { index, member ->
            val col = index % cols
            val row = index / cols
            map[member.id] = Offset(
                x = 150f + col * 250f,
                y = 200f + row * 250f
            )
        }
        map
    }

    Canvas(
        modifier = Modifier
            .fillMaxSize()
            .pointerInput(members) {
                detectTapGestures { tapOffset ->
                    members.forEach { member ->
                        val pos = positions[member.id] ?: return@forEach
                        val distance = sqrt(
                            (tapOffset.x - pos.x) * (tapOffset.x - pos.x) +
                                (tapOffset.y - pos.y) * (tapOffset.y - pos.y)
                        )
                        if (distance < nodeRadius + 10f) {
                            onMemberClick(member)
                        }
                    }
                }
            }
    ) {
        relationships.forEach { rel ->
            val p1 = positions[rel.member_1] ?: return@forEach
            val p2 = positions[rel.member_2] ?: return@forEach
            drawLine(
                color = if (rel.relationship_type_name == "Spouse") Color(0xFFD4956A) else Color(0xFF4A7C6F),
                start = p1,
                end = p2,
                strokeWidth = 3f
            )
        }

        members.forEach { member ->
            val pos = positions[member.id] ?: return@forEach
            drawCircle(color = Color(0xFF4A7C6F), radius = nodeRadius, center = pos)
            drawCircle(color = Color.White, radius = nodeRadius, center = pos, style = Stroke(width = 3f))
            drawContext.canvas.nativeCanvas.drawText(
                member.first_name,
                pos.x,
                pos.y + nodeRadius + 30f,
                android.graphics.Paint().apply {
                    color = android.graphics.Color.parseColor("#1C2826")
                    textSize = 32f
                    textAlign = android.graphics.Paint.Align.CENTER
                }
            )
        }
    }
}
