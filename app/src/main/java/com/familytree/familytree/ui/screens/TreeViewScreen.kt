package com.familytree.familytree.ui.screens

import androidx.compose.foundation.Canvas
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.gestures.detectTapGestures
import androidx.compose.foundation.gestures.rememberTransformableState
import androidx.compose.foundation.gestures.transformable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Add
import androidx.compose.material.icons.filled.ArrowBack
import androidx.compose.material.icons.filled.Remove
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.geometry.CornerRadius
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.geometry.Size
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.Path
import androidx.compose.ui.graphics.TransformOrigin
import androidx.compose.ui.graphics.graphicsLayer
import androidx.compose.ui.graphics.nativeCanvas
import androidx.compose.ui.input.pointer.pointerInput
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.platform.LocalDensity
import androidx.compose.ui.unit.dp
import androidx.navigation.NavController
import com.familytree.familytree.data.models.CreateMemberRequest
import com.familytree.familytree.data.models.FamilyMember
import com.familytree.familytree.data.models.Relationship
import com.familytree.familytree.data.repository.AppRepository
import com.familytree.familytree.ui.navigation.Screen
import com.familytree.familytree.ui.theme.*
import kotlinx.coroutines.launch

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

    // Hoisted here (rather than inside FamilyTreeCanvas) and backed by rememberSaveable so
    // zoom/pan survive navigating to a member profile and back.
    var treeScale by rememberSaveable { mutableStateOf(1.1f) }
    var treeOffsetX by rememberSaveable { mutableStateOf(0f) }
    var treeOffsetY by rememberSaveable { mutableStateOf(0f) }

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
                    scale = treeScale,
                    onScaleChange = { treeScale = it },
                    offset = Offset(treeOffsetX, treeOffsetY),
                    onOffsetChange = { newOffset ->
                        treeOffsetX = newOffset.x
                        treeOffsetY = newOffset.y
                    },
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
    scale: Float,
    onScaleChange: (Float) -> Unit,
    offset: Offset,
    onOffsetChange: (Offset) -> Unit,
    onMemberClick: (FamilyMember) -> Unit
) {
    val density = LocalDensity.current
    val cardWidth = with(density) { 190.dp.toPx() }
    val cardHeight = with(density) { 120.dp.toPx() }
    val hSpacing = with(density) { 260.dp.toPx() }
    val vSpacing = with(density) { 260.dp.toPx() }
    val gridSpacing = with(density) { 40.dp.toPx() }
    val nameTextSize = with(density) { 15.dp.toPx() }
    val dateTextSize = with(density) { 11.dp.toPx() }
    val cardTextPadding = with(density) { 16.dp.toPx() }

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

    val transformState = rememberTransformableState { zoomChange, panChange, _ ->
        onScaleChange((scale * zoomChange).coerceIn(0.3f, 3f))
        onOffsetChange(offset + panChange)
    }

    Box(
        modifier = Modifier
            .fillMaxSize()
            .transformable(state = transformState)
            .pointerInput(members, positions, scale, offset) {
                detectTapGestures { tapOffset ->
                    // pointerInput here sits outside the Canvas's graphicsLayer, so it only
                    // ever sees raw screen coordinates - convert back into canvas/content
                    // space using the current scale and pan offset. transformOrigin on the
                    // graphicsLayer is pinned to the top-left so this stays a plain linear
                    // inverse (no extra center-of-layer correction needed).
                    val canvasX = (tapOffset.x - offset.x) / scale
                    val canvasY = (tapOffset.y - offset.y) / scale

                    val hitMember = members.firstOrNull { member ->
                        val pos = positions[member.id] ?: return@firstOrNull false
                        canvasX in (pos.x - cardWidth / 2)..(pos.x + cardWidth / 2) &&
                            canvasY in (pos.y - cardHeight / 2)..(pos.y + cardHeight / 2)
                    }
                    hitMember?.let { onMemberClick(it) }
                }
            }
    ) {
        Canvas(
            modifier = Modifier
                .fillMaxSize()
                .graphicsLayer {
                    scaleX = scale
                    scaleY = scale
                    translationX = offset.x
                    translationY = offset.y
                    transformOrigin = TransformOrigin(0f, 0f)
                }
        ) {
            // Subtle graph-paper grid background
            val gridColor = Color(0x0F1C2826)
            var gx = 0f
            while (gx < size.width) {
                drawLine(gridColor, Offset(gx, 0f), Offset(gx, size.height), strokeWidth = 1f)
                gx += gridSpacing
            }
            var gy = 0f
            while (gy < size.height) {
                drawLine(gridColor, Offset(0f, gy), Offset(size.width, gy), strokeWidth = 1f)
                gy += gridSpacing
            }

            // Draw relationship connector lines first, underneath the cards
            relationships.forEach { rel ->
                val p1 = positions[rel.member_1] ?: return@forEach
                val p2 = positions[rel.member_2] ?: return@forEach
                val isSpouse = rel.relationship_type_name in spouseRelTypes
                val isParentChild = rel.relationship_type_name in parentRelTypes ||
                    rel.relationship_type_name in childRelTypes

                when {
                    isSpouse -> {
                        // Horizontal double line between spouse cards on the same row
                        val left = if (p1.x <= p2.x) p1 else p2
                        val right = if (p1.x <= p2.x) p2 else p1
                        val startX = left.x + cardWidth / 2
                        val endX = right.x - cardWidth / 2
                        val midY = (left.y + right.y) / 2
                        drawLine(
                            color = Color(0xFFD4956A),
                            start = Offset(startX, midY - 3f),
                            end = Offset(endX, midY - 3f),
                            strokeWidth = 2.5f
                        )
                        drawLine(
                            color = Color(0xFFD4956A),
                            start = Offset(startX, midY + 3f),
                            end = Offset(endX, midY + 3f),
                            strokeWidth = 2.5f
                        )
                    }
                    isParentChild -> {
                        // Right-angle elbow: down from parent bottom, across, down into child top
                        val genOf1 = generations[rel.member_1] ?: 0
                        val genOf2 = generations[rel.member_2] ?: 0
                        val parent = if (genOf1 <= genOf2) p1 else p2
                        val child = if (genOf1 <= genOf2) p2 else p1

                        val parentBottom = Offset(parent.x, parent.y + cardHeight / 2)
                        val childTop = Offset(child.x, child.y - cardHeight / 2)
                        val midY = (parentBottom.y + childTop.y) / 2

                        val path = Path().apply {
                            moveTo(parentBottom.x, parentBottom.y)
                            lineTo(parentBottom.x, midY)
                            lineTo(childTop.x, midY)
                            lineTo(childTop.x, childTop.y)
                        }
                        drawPath(
                            path = path,
                            color = Color(0xFF4A7C6F),
                            style = androidx.compose.ui.graphics.drawscope.Stroke(width = 2.5f)
                        )
                    }
                    else -> {
                        drawLine(
                            color = Color(0xFF4A7C6F),
                            start = p1,
                            end = p2,
                            strokeWidth = 2.5f
                        )
                    }
                }
            }

            // Draw member cards on top
            members.forEach { member ->
                val pos = positions[member.id] ?: return@forEach
                val left = pos.x - cardWidth / 2
                val top = pos.y - cardHeight / 2
                val cornerRadius = CornerRadius(16f, 16f)

                // Drop shadow
                drawRoundRect(
                    color = Color(0x1A2E5C51),
                    topLeft = Offset(left, top + 4f),
                    size = Size(cardWidth, cardHeight),
                    cornerRadius = cornerRadius
                )

                // Card background
                drawRoundRect(
                    color = Color.White,
                    topLeft = Offset(left, top),
                    size = Size(cardWidth, cardHeight),
                    cornerRadius = cornerRadius
                )

                // Card border accent
                drawRoundRect(
                    color = Color(0xFF4A7C6F),
                    topLeft = Offset(left, top),
                    size = Size(cardWidth, cardHeight),
                    cornerRadius = cornerRadius,
                    style = androidx.compose.ui.graphics.drawscope.Stroke(width = 1.5f)
                )

                val namePaint = android.graphics.Paint().apply {
                    color = android.graphics.Color.parseColor("#1C2826")
                    textSize = nameTextSize
                    textAlign = android.graphics.Paint.Align.CENTER
                    typeface = android.graphics.Typeface.DEFAULT_BOLD
                }
                val datePaint = android.graphics.Paint().apply {
                    color = android.graphics.Color.parseColor("#5A6B67")
                    textSize = dateTextSize
                    textAlign = android.graphics.Paint.Align.CENTER
                    typeface = android.graphics.Typeface.DEFAULT
                }

                val fullName = listOf(member.first_name, member.last_name)
                    .filter { it.isNotBlank() }
                    .joinToString(" ")
                val maxTextWidth = cardWidth - cardTextPadding
                // Split into first/last name lines if the full name won't fit on one line
                val nameLines = if (
                    member.last_name.isNotBlank() &&
                    namePaint.measureText(fullName) > maxTextWidth
                ) {
                    listOf(member.first_name, member.last_name)
                } else {
                    listOf(fullName)
                }
                val birthDate = member.birth_date?.takeIf { it.isNotBlank() }

                val nameLineHeight = nameTextSize * 1.25f
                val dateLineHeight = dateTextSize * 1.6f
                val blockHeight = nameLines.size * nameLineHeight + (if (birthDate != null) dateLineHeight else 0f)

                var textY = pos.y - blockHeight / 2f + nameLineHeight * 0.75f
                nameLines.forEach { line ->
                    drawContext.canvas.nativeCanvas.drawText(line, pos.x, textY, namePaint)
                    textY += nameLineHeight
                }

                if (birthDate != null) {
                    textY += dateLineHeight * 0.55f
                    drawContext.canvas.nativeCanvas.drawText(birthDate, pos.x, textY, datePaint)
                }
            }
        }

        Column(
            modifier = Modifier
                .align(Alignment.BottomEnd)
                .padding(end = 16.dp, bottom = 90.dp)
        ) {
            ZoomButton(icon = Icons.Default.Add) {
                onScaleChange((scale + 0.15f).coerceIn(0.3f, 3f))
            }
            Spacer(Modifier.height(10.dp))
            ZoomButton(icon = Icons.Default.Remove) {
                onScaleChange((scale - 0.15f).coerceIn(0.3f, 3f))
            }
        }
    }
}

@Composable
private fun ZoomButton(icon: androidx.compose.ui.graphics.vector.ImageVector, onClick: () -> Unit) {
    Box(
        modifier = Modifier
            .size(44.dp)
            .background(Color.White, CircleShape)
            .border(1.dp, Color(0xFF4A7C6F).copy(alpha = 0.3f), CircleShape)
            .clickable(onClick = onClick),
        contentAlignment = Alignment.Center
    ) {
        Icon(icon, contentDescription = null, tint = Color(0xFF4A7C6F))
    }
}
