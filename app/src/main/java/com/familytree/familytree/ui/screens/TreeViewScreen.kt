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
                FamilyTreeCanvas(
                    members = members,
                    relationships = relationships,
                    onMemberClick = { member ->
                        navController.navigate(Screen.MemberDetail.createRoute(member.id))
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
fun FamilyTreeCanvas(
    members: List<FamilyMember>,
    relationships: List<Relationship>,
    onMemberClick: (FamilyMember) -> Unit
) {
    val nodeRadius = 55f
    val hSpacing = 220f
    val vSpacing = 200f

    val parentRelTypes = listOf(
        "Father", "Mother", "Grandfather", "Grandmother",
        "Great Grandfather", "Great Grandmother",
        "Stepfather", "Stepmother", "Guardian"
    )
    val childRelTypes = listOf(
        "Son", "Daughter", "Grandson", "Granddaughter",
        "Great Grandson", "Great Granddaughter",
        "Stepson", "Stepdaughter", "Step Son", "Step Daughter",
        "Adopted Son", "Adopted Daughter"
    )
    val spouseRelTypes = listOf(
        "Spouse", "Husband", "Wife", "Partner", "Fiance", "Fiancee"
    )

    // Build children map for layout
    val childrenOf = remember(members, relationships) {
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

    // Assign generations using BFS
    val generations = remember(members, relationships) {
        val hasParent = mutableSetOf<Int>()
        relationships.forEach { rel ->
            if (rel.relationship_type_name in parentRelTypes) hasParent.add(rel.member_2)
            if (rel.relationship_type_name in childRelTypes) hasParent.add(rel.member_1)
        }
        val roots = members.filter { it.id !in hasParent }.map { it.id }
        val gen = mutableMapOf<Int, Int>()
        val queue = ArrayDeque<Int>()
        roots.forEach { id -> gen[id] = 0; queue.add(id) }
        while (queue.isNotEmpty()) {
            val cur = queue.removeFirst()
            childrenOf[cur]?.forEach { childId ->
                if (childId !in gen) {
                    gen[childId] = (gen[cur] ?: 0) + 1
                    queue.add(childId)
                }
            }
        }
        members.forEach { m -> if (m.id !in gen) gen[m.id] = 0 }
        gen
    }

    // Calculate positions - clean grid by generation
    val positions = remember(members, relationships) {
        val map = mutableMapOf<Int, Offset>()
        val byGen = members.groupBy { generations[it.id] ?: 0 }
        val canvasWidth = ((byGen.values.maxOfOrNull { it.size } ?: 1) + 1) * hSpacing

        byGen.forEach { (gen, genMembers) ->
            val totalWidth = genMembers.size * hSpacing
            val startX = (canvasWidth - totalWidth) / 2f + hSpacing / 2f
            genMembers.forEachIndexed { index, member ->
                map[member.id] = Offset(
                    x = startX + index * hSpacing,
                    y = 150f + gen * vSpacing
                )
            }
        }
        map
    }

    var scale by remember { mutableStateOf(0.85f) }
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
                .graphicsLayer {
                    scaleX = scale
                    scaleY = scale
                    translationX = offset.x
                    translationY = offset.y
                }
                .pointerInput(members, positions) {
                    detectTapGestures { tapOffset ->
                        val canvasX = tapOffset.x
                        val canvasY = tapOffset.y

                        // Find the closest member to the tap
                        var closestMember: FamilyMember? = null
                        var closestDistance = Float.MAX_VALUE

                        members.forEach { member ->
                            val pos = positions[member.id] ?: return@forEach
                            val distance = sqrt(
                                (canvasX - pos.x) * (canvasX - pos.x) +
                                (canvasY - pos.y) * (canvasY - pos.y)
                            )
                            if (distance < closestDistance) {
                                closestDistance = distance
                                closestMember = member
                            }
                        }

                        // Only trigger if tap is within node radius
                        if (closestDistance < nodeRadius + 25f) {
                            closestMember?.let { onMemberClick(it) }
                        }
                    }
                }
        ) {
            // Draw relationship lines first
            relationships.forEach { rel ->
                val p1 = positions[rel.member_1] ?: return@forEach
                val p2 = positions[rel.member_2] ?: return@forEach
                val isSpouse = rel.relationship_type_name in spouseRelTypes
                drawLine(
                    color = if (isSpouse) Color(0xFFD4956A) else Color(0xFF4A7C6F),
                    start = p1,
                    end = p2,
                    strokeWidth = 2.5f,
                    pathEffect = if (isSpouse) androidx.compose.ui.graphics.PathEffect.dashPathEffect(
                        floatArrayOf(10f, 5f)
                    ) else null
                )
            }

            // Draw nodes on top
            members.forEach { member ->
                val pos = positions[member.id] ?: return@forEach

                // Shadow
                drawCircle(
                    color = Color(0x1A2E5C51),
                    radius = nodeRadius + 4f,
                    center = pos.copy(y = pos.y + 4f)
                )

                // Circle
                drawCircle(color = Color(0xFF4A7C6F), radius = nodeRadius, center = pos)
                drawCircle(
                    color = Color.White,
                    radius = nodeRadius,
                    center = pos,
                    style = androidx.compose.ui.graphics.drawscope.Stroke(width = 3f)
                )

                // Initial inside circle
                drawContext.canvas.nativeCanvas.drawText(
                    member.first_name.take(1).uppercase(),
                    pos.x,
                    pos.y + 12f,
                    android.graphics.Paint().apply {
                        color = android.graphics.Color.WHITE
                        textSize = 36f
                        textAlign = android.graphics.Paint.Align.CENTER
                        typeface = android.graphics.Typeface.DEFAULT_BOLD
                    }
                )

                // Name below circle
                drawContext.canvas.nativeCanvas.drawText(
                    member.first_name,
                    pos.x,
                    pos.y + nodeRadius + 30f,
                    android.graphics.Paint().apply {
                        color = android.graphics.Color.parseColor("#1C2826")
                        textSize = 28f
                        textAlign = android.graphics.Paint.Align.CENTER
                        typeface = android.graphics.Typeface.DEFAULT
                    }
                )
            }
        }
    }
}
