package com.familytree.familytree.ui.screens

import androidx.compose.foundation.Canvas
import androidx.compose.foundation.gestures.detectTapGestures
import androidx.compose.foundation.gestures.rememberTransformableState
import androidx.compose.foundation.gestures.transformable
import androidx.compose.foundation.layout.*
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Add
import androidx.compose.material.icons.filled.ArrowBack
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.graphicsLayer
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
import com.familytree.familytree.ui.theme.*
import kotlinx.coroutines.launch
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
    var focusedMemberId by remember { mutableStateOf<Int?>(null) }

    fun loadData() {
        scope.launch {
            val membersResult = repository.getFamilyMembers(treeId)
            val relsResult = repository.getRelationships(treeId)
            if (membersResult.isSuccess) {
                members = membersResult.getOrNull() ?: emptyList()
                if (focusedMemberId == null && members.isNotEmpty()) {
                    focusedMemberId = members.first().id
                }
            }
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
                        Icon(Icons.Default.ArrowBack, contentDescription = "Back", tint = Color.White)
                    }
                },
                actions = {
                    IconButton(onClick = { showAddMember = true }) {
                        Icon(Icons.Default.Add, contentDescription = "Add", tint = Color.White)
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
                AncestryTreeCanvas(
                    members = members,
                    relationships = relationships,
                    focusedMemberId = focusedMemberId ?: members.first().id,
                    onMemberClick = { member ->
                        focusedMemberId = member.id
                        navController.navigate(Screen.MemberDetail.createRoute(member.id))
                    },
                    onMemberFocus = { member ->
                        focusedMemberId = member.id
                    }
                )
                Button(
                    onClick = { showAddMember = true },
                    modifier = Modifier
                        .align(Alignment.BottomCenter)
                        .fillMaxWidth()
                        .padding(16.dp),
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
fun AncestryTreeCanvas(
    members: List<FamilyMember>,
    relationships: List<Relationship>,
    focusedMemberId: Int,
    onMemberClick: (FamilyMember) -> Unit,
    onMemberFocus: (FamilyMember) -> Unit
) {
    val nodeRadius = 55f
    val hSpacing = 220f
    val vSpacing = 200f

    val parentRelTypes = listOf(
        "Father", "Mother", "Grandfather", "Grandmother",
        "Great Grandfather", "Great Grandmother",
        "Stepfather", "Stepmother", "Guardian",
        "Adopted Father", "Adopted Mother"
    )

    val childRelTypes = listOf(
        "Son", "Daughter", "Grandson", "Granddaughter",
        "Great Grandson", "Great Granddaughter",
        "Stepson", "Stepdaughter", "Step Son", "Step Daughter",
        "Adopted Son", "Adopted Daughter"
    )

    val spouseRelTypes = listOf(
        "Spouse", "Husband", "Wife", "Partner",
        "Fiance", "Fiancee"
    )

    val parentOf = remember(members, relationships) {
        val map = mutableMapOf<Int, MutableList<Int>>()
        relationships.forEach { rel ->
            if (rel.relationship_type_name in parentRelTypes) {
                map.getOrPut(rel.member_2) { mutableListOf() }.add(rel.member_1)
            }
            if (rel.relationship_type_name in childRelTypes) {
                map.getOrPut(rel.member_1) { mutableListOf() }.add(rel.member_2)
            }
        }
        map
    }

    val childOf = remember(members, relationships) {
        val map = mutableMapOf<Int, MutableList<Int>>()
        relationships.forEach { rel ->
            if (rel.relationship_type_name in parentRelTypes) {
                map.getOrPut(rel.member_1) { mutableListOf() }.add(rel.member_2)
            }
            if (rel.relationship_type_name in childRelTypes) {
                map.getOrPut(rel.member_2) { mutableListOf() }.add(rel.member_1)
            }
        }
        map
    }

    val spouseOf = remember(members, relationships) {
        val map = mutableMapOf<Int, MutableList<Int>>()
        relationships.forEach { rel ->
            if (rel.relationship_type_name in spouseRelTypes) {
                map.getOrPut(rel.member_1) { mutableListOf() }.add(rel.member_2)
                map.getOrPut(rel.member_2) { mutableListOf() }.add(rel.member_1)
            }
        }
        map
    }

    val visibleMembers = remember(focusedMemberId, members, relationships) {
        val visible = mutableSetOf<Int>()
        visible.add(focusedMemberId)
        // Parents
        childOf[focusedMemberId]?.forEach { visible.add(it) }
        // Grandparents
        childOf[focusedMemberId]?.forEach { parentId ->
            childOf[parentId]?.forEach { visible.add(it) }
        }
        // Children
        parentOf[focusedMemberId]?.forEach { visible.add(it) }
        // Grandchildren
        parentOf[focusedMemberId]?.forEach { childId ->
            parentOf[childId]?.forEach { visible.add(it) }
        }
        // Spouses of all visible
        visible.toList().forEach { id ->
            spouseOf[id]?.forEach { visible.add(it) }
        }
        members.filter { it.id in visible }
    }

    val positions = remember(focusedMemberId, visibleMembers, relationships) {
        val map = mutableMapOf<Int, Offset>()
        val centerX = 600f
        val focusedY = 500f

        map[focusedMemberId] = Offset(centerX, focusedY)

        // Spouses next to focused
        spouseOf[focusedMemberId]?.forEachIndexed { i, spouseId ->
            map[spouseId] = Offset(centerX + hSpacing * (i + 1), focusedY)
        }

        // Parents above
        val parents = childOf[focusedMemberId] ?: emptyList()
        val parentStartX = centerX - (parents.size - 1) * hSpacing / 2f
        parents.forEachIndexed { i, parentId ->
            val parentX = parentStartX + i * hSpacing
            map[parentId] = Offset(parentX, focusedY - vSpacing)
            // Grandparents
            val grandparents = childOf[parentId] ?: emptyList()
            val gpStartX = parentX - (grandparents.size - 1) * hSpacing / 2f
            grandparents.forEachIndexed { j, gpId ->
                if (gpId !in map) map[gpId] = Offset(gpStartX + j * hSpacing, focusedY - vSpacing * 2)
            }
            // Parent spouses
            spouseOf[parentId]?.forEach { spouseId ->
                if (spouseId !in map) map[spouseId] = Offset(parentX + hSpacing, focusedY - vSpacing)
            }
        }

        // Children below
        val children = parentOf[focusedMemberId] ?: emptyList()
        val childStartX = centerX - (children.size - 1) * hSpacing / 2f
        children.forEachIndexed { i, childId ->
            val childX = childStartX + i * hSpacing
            if (childId !in map) map[childId] = Offset(childX, focusedY + vSpacing)
            // Grandchildren
            val grandchildren = parentOf[childId] ?: emptyList()
            val gcStartX = childX - (grandchildren.size - 1) * hSpacing / 2f
            grandchildren.forEachIndexed { j, gcId ->
                if (gcId !in map) map[gcId] = Offset(gcStartX + j * hSpacing, focusedY + vSpacing * 2)
            }
        }

        map
    }

    // Pinch to zoom and pan
    var scale by remember { mutableStateOf(1f) }
    var offset by remember { mutableStateOf(Offset.Zero) }
    val transformState = rememberTransformableState { zoomChange, panChange, _ ->
        scale = (scale * zoomChange).coerceIn(0.3f, 3f)
        offset += panChange
    }

    Box(
        modifier = Modifier
            .fillMaxSize()
            .transformable(state = transformState)
    ) {
        Canvas(
            modifier = Modifier
                .fillMaxSize()
                .pointerInput(visibleMembers, scale, offset) {
                    detectTapGestures { tapOffset ->
                        // Convert screen coordinates to canvas coordinates
                        val canvasX = (tapOffset.x - offset.x) / scale
                        val canvasY = (tapOffset.y - offset.y) / scale

                        var tapped = false
                        visibleMembers.forEach { member ->
                            if (tapped) return@forEach
                            val pos = positions[member.id] ?: return@forEach
                            val radius = if (member.id == focusedMemberId) nodeRadius + 8f else nodeRadius
                            val distance = sqrt(
                                (canvasX - pos.x) * (canvasX - pos.x) +
                                (canvasY - pos.y) * (canvasY - pos.y)
                            )
                            if (distance < radius + 20f) {
                                tapped = true
                                if (member.id == focusedMemberId) {
                                    onMemberClick(member)
                                } else {
                                    onMemberFocus(member)
                                }
                            }
                        }
                    }
                }
                .graphicsLayer {
                    scaleX = scale
                    scaleY = scale
                    translationX = offset.x
                    translationY = offset.y
                }
        ) {
            // Draw lines
            relationships.forEach { rel ->
                val p1 = positions[rel.member_1] ?: return@forEach
                val p2 = positions[rel.member_2] ?: return@forEach
                val isSpouse = rel.relationship_type_name in spouseRelTypes
                drawLine(
                    color = if (isSpouse) Color(0xFFD4956A) else Color(0xFF4A7C6F),
                    start = p1,
                    end = p2,
                    strokeWidth = 2.5f,
                    pathEffect = if (isSpouse) androidx.compose.ui.graphics.PathEffect.dashPathEffect(floatArrayOf(10f, 5f)) else null
                )
            }

            // Draw nodes
            visibleMembers.forEach { member ->
                val pos = positions[member.id] ?: return@forEach
                val isFocused = member.id == focusedMemberId

                // Shadow
                drawCircle(
                    color = Color(0x1A2E5C51),
                    radius = nodeRadius + 4f,
                    center = pos.copy(y = pos.y + 4f)
                )

                // Circle - focused member is slightly larger and brighter
                drawCircle(
                    color = if (isFocused) Color(0xFF2E5C51) else Color(0xFF4A7C6F),
                    radius = if (isFocused) nodeRadius + 8f else nodeRadius,
                    center = pos
                )
                drawCircle(
                    color = Color.White,
                    radius = if (isFocused) nodeRadius + 8f else nodeRadius,
                    center = pos,
                    style = androidx.compose.ui.graphics.drawscope.Stroke(width = if (isFocused) 4f else 2.5f)
                )

                // Initial
                drawContext.canvas.nativeCanvas.drawText(
                    member.first_name.take(1).uppercase(),
                    pos.x,
                    pos.y + 12f,
                    android.graphics.Paint().apply {
                        color = android.graphics.Color.WHITE
                        textSize = if (isFocused) 42f else 36f
                        textAlign = android.graphics.Paint.Align.CENTER
                        typeface = android.graphics.Typeface.DEFAULT_BOLD
                    }
                )

                // Name label
                drawContext.canvas.nativeCanvas.drawText(
                    member.first_name,
                    pos.x,
                    pos.y + (if (isFocused) nodeRadius + 20f else nodeRadius + 16f) + 16f,
                    android.graphics.Paint().apply {
                        color = android.graphics.Color.parseColor("#1C2826")
                        textSize = if (isFocused) 30f else 26f
                        textAlign = android.graphics.Paint.Align.CENTER
                        typeface = if (isFocused) android.graphics.Typeface.DEFAULT_BOLD else android.graphics.Typeface.DEFAULT
                    }
                )

                // "Tap to view" hint for focused member
                if (isFocused) {
                    drawContext.canvas.nativeCanvas.drawText(
                        "tap to view profile",
                        pos.x,
                        pos.y + nodeRadius + 52f,
                        android.graphics.Paint().apply {
                            color = android.graphics.Color.parseColor("#8A9B97")
                            textSize = 22f
                            textAlign = android.graphics.Paint.Align.CENTER
                        }
                    )
                }
            }
        }

        // Generation labels
        Column(
            modifier = Modifier
                .align(Alignment.TopStart)
                .padding(16.dp)
        ) {
            if (childOf[focusedMemberId]?.isNotEmpty() == true) {
                Text("👆 Tap to explore ancestors", color = TextHint, fontSize = androidx.compose.ui.unit.TextUnit.Unspecified)
            }
        }
    }
}
