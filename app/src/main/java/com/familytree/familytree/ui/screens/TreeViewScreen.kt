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
import androidx.compose.foundation.shape.RoundedCornerShape
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
import androidx.compose.ui.graphics.PathEffect
import androidx.compose.ui.graphics.StrokeCap
import androidx.compose.ui.graphics.TransformOrigin
import androidx.compose.ui.graphics.drawscope.DrawScope
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.graphics.graphicsLayer
import androidx.compose.ui.graphics.nativeCanvas
import androidx.compose.ui.input.pointer.pointerInput
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.platform.LocalDensity
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
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

// ---------------------------------------------------------------------------------------
// Relationship classification
// ---------------------------------------------------------------------------------------

private val spouseRelTypes = setOf("Spouse", "Husband", "Wife", "Partner", "Fiance", "Fiancee")

// relationship_type_name describes what member_1 IS to member_2 (e.g. "Father" means
// member_1 is member_2's father).
private val bioParentTypes = setOf("Father", "Mother", "Grandfather", "Grandmother")
private val bioChildTypes = setOf("Son", "Daughter", "Grandson", "Granddaughter")
private val stepParentTypes = setOf("Stepfather", "Stepmother", "Step Father", "Step Mother")
private val stepChildTypes = setOf("Stepson", "Stepdaughter", "Step Son", "Step Daughter")
private val stepSiblingTypes = setOf("Step Brother", "Step Sister")
private val adoptedChildTypes = setOf("Adopted Son", "Adopted Daughter")
private val adoptedSiblingTypes = setOf("Adopted Brother", "Adopted Sister")

private enum class RelCategory { BIO, STEP, ADOPTED }

private data class ParentEdge(val parentId: Int, val childId: Int, val category: RelCategory)

private class TreeUnit(val id: String, val partners: List<Int>, val children: List<Int>)

private sealed class RenderNode {
    var width: Float = 0f
}
private class UnitNode(val unit: TreeUnit, val childNodes: List<RenderNode>) : RenderNode()
private class LeafNode(val personId: Int) : RenderNode()

private class TreeLayoutResult(
    val positions: Map<Int, Offset>,
    val genOfPerson: Map<Int, Int>,
    val units: List<TreeUnit>,
    val couples: List<Pair<Int, Int>>,
    val siblingLines: List<Triple<Int, Int, RelCategory>>,
    val childCategory: Map<Int, RelCategory>
)

// ---------------------------------------------------------------------------------------
// Layout engine - builds "family units" (a couple, or a single parent, plus their children),
// starts from the oldest generation (people with no parents in the tree) and recursively
// positions each unit's children centered underneath it, using subtree-width calculation so
// nothing overlaps. Each person is placed exactly once.
// ---------------------------------------------------------------------------------------

private fun buildTreeLayout(
    members: List<FamilyMember>,
    relationships: List<Relationship>,
    cardWidth: Float,
    spouseGap: Float,
    siblingGap: Float,
    vSpacing: Float,
    treeGap: Float,
    topMargin: Float
): TreeLayoutResult {
    val parentEdges = mutableListOf<ParentEdge>()
    relationships.forEach { rel ->
        val name = rel.relationship_type_name
        when {
            name in bioParentTypes -> parentEdges += ParentEdge(rel.member_1, rel.member_2, RelCategory.BIO)
            name in bioChildTypes -> parentEdges += ParentEdge(rel.member_2, rel.member_1, RelCategory.BIO)
            name in stepParentTypes -> parentEdges += ParentEdge(rel.member_1, rel.member_2, RelCategory.STEP)
            name in stepChildTypes -> parentEdges += ParentEdge(rel.member_2, rel.member_1, RelCategory.STEP)
            name in adoptedChildTypes -> parentEdges += ParentEdge(rel.member_2, rel.member_1, RelCategory.ADOPTED)
        }
    }

    val childrenOf = parentEdges.groupBy { it.parentId }.mapValues { e -> e.value.map { it.childId }.distinct() }

    // Best relationship category found for each child (bio > step > adopted), used to style
    // that child's incoming connector branch.
    val childCategory = mutableMapOf<Int, RelCategory>()
    val priority = mapOf(RelCategory.BIO to 3, RelCategory.STEP to 2, RelCategory.ADOPTED to 1)
    parentEdges.forEach { e ->
        val existing = childCategory[e.childId]
        if (existing == null || (priority[e.category] ?: 0) > (priority[existing] ?: 0)) {
            childCategory[e.childId] = e.category
        }
    }

    // Distinct spouse couples.
    val couples = run {
        val seen = mutableSetOf<Pair<Int, Int>>()
        val list = mutableListOf<Pair<Int, Int>>()
        relationships.forEach { rel ->
            if (rel.relationship_type_name in spouseRelTypes) {
                val pair = minOf(rel.member_1, rel.member_2) to maxOf(rel.member_1, rel.member_2)
                if (seen.add(pair)) list.add(pair)
            }
        }
        list
    }

    // Step/adopted sibling relationships are not parent-child edges (they don't drive layout),
    // but they still get a direct dashed/dotted connector drawn between the two cards.
    val siblingLines = run {
        val seen = mutableSetOf<Pair<Int, Int>>()
        val list = mutableListOf<Triple<Int, Int, RelCategory>>()
        relationships.forEach { rel ->
            val cat = when (rel.relationship_type_name) {
                in stepSiblingTypes -> RelCategory.STEP
                in adoptedSiblingTypes -> RelCategory.ADOPTED
                else -> null
            } ?: return@forEach
            val pair = minOf(rel.member_1, rel.member_2) to maxOf(rel.member_1, rel.member_2)
            if (seen.add(pair)) list.add(Triple(pair.first, pair.second, cat))
        }
        list
    }

    // Build family units. Every spouse couple becomes a unit (so the two cards render
    // together even if childless); any remaining unpartnered parent with children becomes a
    // solo unit. Each child is claimed by exactly one unit (first match wins) so nobody is
    // ever positioned - or drawn - twice.
    val assignedChildren = mutableSetOf<Int>()
    val partneredPersons = mutableSetOf<Int>()
    val unitsList = mutableListOf<TreeUnit>()
    val headUnitOfPerson = mutableMapOf<Int, String>()

    couples.forEach { (a, b) ->
        val kids = (childrenOf[a].orEmpty() + childrenOf[b].orEmpty()).distinct().filter { it !in assignedChildren }
        val id = "u_${a}_$b"
        unitsList += TreeUnit(id, listOf(a, b), kids)
        headUnitOfPerson[a] = id
        headUnitOfPerson[b] = id
        assignedChildren += kids
        partneredPersons += a
        partneredPersons += b
    }
    members.forEach { m ->
        if (m.id in partneredPersons) return@forEach
        val kids = childrenOf[m.id].orEmpty().filter { it !in assignedChildren }
        if (kids.isNotEmpty()) {
            val id = "u_solo_${m.id}"
            unitsList += TreeUnit(id, listOf(m.id), kids)
            headUnitOfPerson[m.id] = id
            assignedChildren += kids
        }
    }

    val parentUnitOfChild = mutableMapOf<Int, String>()
    unitsList.forEach { u -> u.children.forEach { childId -> parentUnitOfChild[childId] = u.id } }

    // Root units: couples/solo-parents whose partners aren't anyone's child in the tree -
    // i.e. the oldest known generation for that branch.
    val rootUnits = unitsList.filter { u -> u.partners.none { it in parentUnitOfChild } }

    val builtUnitIds = mutableSetOf<String>()
    val renderedIds = mutableSetOf<Int>()

    fun buildNode(personId: Int): RenderNode {
        val unitId = headUnitOfPerson[personId]
        if (unitId != null && unitId !in builtUnitIds) {
            builtUnitIds += unitId
            val unit = unitsList.first { it.id == unitId }
            unit.partners.forEach { renderedIds += it }
            val childNodes = unit.children.map { buildNode(it) }
            return UnitNode(unit, childNodes)
        }
        renderedIds += personId
        return LeafNode(personId)
    }

    val forest = mutableListOf<RenderNode>()
    rootUnits.forEach { u ->
        if (u.id !in builtUnitIds) {
            forest += buildNode(u.partners.first())
        }
    }
    // Anyone left over (isolated individuals with no recorded relationships at all) still
    // needs to appear on the tree exactly once.
    members.forEach { m ->
        if (m.id !in renderedIds) {
            forest += buildNode(m.id)
        }
    }

    fun computeWidth(node: RenderNode): Float {
        val w = when (node) {
            is UnitNode -> {
                val ownWidth = if (node.unit.partners.size == 2) 2 * cardWidth + spouseGap else cardWidth
                if (node.childNodes.isEmpty()) {
                    ownWidth
                } else {
                    val childrenWidth = node.childNodes.sumOf { computeWidth(it).toDouble() }.toFloat() +
                        (node.childNodes.size - 1) * siblingGap
                    maxOf(ownWidth, childrenWidth)
                }
            }
            is LeafNode -> cardWidth
        }
        node.width = w
        return w
    }
    forest.forEach { computeWidth(it) }

    val positions = mutableMapOf<Int, Offset>()
    val genOfPerson = mutableMapOf<Int, Int>()

    fun place(node: RenderNode, leftEdge: Float, depth: Int) {
        val centerX = leftEdge + node.width / 2f
        val y = topMargin + depth * vSpacing
        when (node) {
            is UnitNode -> {
                if (node.unit.partners.size == 2) {
                    positions[node.unit.partners[0]] = Offset(centerX - (cardWidth + spouseGap) / 2f, y)
                    positions[node.unit.partners[1]] = Offset(centerX + (cardWidth + spouseGap) / 2f, y)
                } else {
                    positions[node.unit.partners[0]] = Offset(centerX, y)
                }
                node.unit.partners.forEach { genOfPerson[it] = depth }
                if (node.childNodes.isNotEmpty()) {
                    val totalChildWidth = node.childNodes.sumOf { it.width.toDouble() }.toFloat() +
                        (node.childNodes.size - 1) * siblingGap
                    var cursor = centerX - totalChildWidth / 2f
                    node.childNodes.forEach { child ->
                        place(child, cursor, depth + 1)
                        cursor += child.width + siblingGap
                    }
                }
            }
            is LeafNode -> {
                positions[node.personId] = Offset(centerX, y)
                genOfPerson[node.personId] = depth
            }
        }
    }

    var cursor = 0f
    forest.forEach { root ->
        place(root, cursor, 0)
        cursor += root.width + treeGap
    }

    return TreeLayoutResult(positions, genOfPerson, unitsList, couples, siblingLines, childCategory)
}

private fun personBorderColor(personId: Int, layout: TreeLayoutResult): Color {
    if (personId in layout.childCategory) return Color(0xFF4A7C6F)
    val inCouple = layout.couples.any { it.first == personId || it.second == personId }
    return if (inCouple) Color(0xFFD4956A) else Color(0xFF9AA6A3)
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
    val cardWidth = with(density) { 180.dp.toPx() }
    val cardHeight = with(density) { 80.dp.toPx() }
    val spouseGap = with(density) { 20.dp.toPx() }
    val siblingGap = with(density) { 36.dp.toPx() }
    val vSpacing = with(density) { 190.dp.toPx() }
    val treeGap = with(density) { 90.dp.toPx() }
    val topMargin = with(density) { 90.dp.toPx() }
    val dotSpacing = with(density) { 30.dp.toPx() }
    val avatarRadius = with(density) { 16.dp.toPx() }
    val cardPadding = with(density) { 14.dp.toPx() }
    val nameTextSize = with(density) { 14.dp.toPx() }
    val dateTextSize = with(density) { 11.dp.toPx() }
    val labelTextSize = with(density) { 12.dp.toPx() }

    val layout = remember(members, relationships, cardWidth, spouseGap, siblingGap, vSpacing, treeGap, topMargin) {
        buildTreeLayout(members, relationships, cardWidth, spouseGap, siblingGap, vSpacing, treeGap, topMargin)
    }
    val positions = layout.positions

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
            // Subtle dot-grid background
            val dotColor = Color(0x1F1C2826)
            var gx = 0f
            while (gx < size.width) {
                var gy = 0f
                while (gy < size.height) {
                    drawCircle(dotColor, radius = 1.6f, center = Offset(gx, gy))
                    gy += dotSpacing
                }
                gx += dotSpacing
            }

            val bioColor = Color(0xFF4A7C6F)
            val spouseColor = Color(0xFFD4956A)
            val dashedEffect = PathEffect.dashPathEffect(floatArrayOf(16f, 10f), 0f)
            val dottedEffect = PathEffect.dashPathEffect(floatArrayOf(2f, 9f), 0f)

            fun connectorEffect(cat: RelCategory): PathEffect? = when (cat) {
                RelCategory.BIO -> null
                RelCategory.STEP -> dashedEffect
                RelCategory.ADOPTED -> dottedEffect
            }

            // Generation labels along the left edge
            if (positions.isNotEmpty()) {
                val minX = positions.values.minOf { it.x } - cardWidth / 2f
                val labelPaint = android.graphics.Paint().apply {
                    color = android.graphics.Color.parseColor("#8A9A96")
                    textSize = labelTextSize
                    textAlign = android.graphics.Paint.Align.LEFT
                    typeface = android.graphics.Typeface.DEFAULT
                }
                val maxGen = layout.genOfPerson.values.maxOrNull() ?: 0
                for (gen in 0..maxGen) {
                    val y = topMargin + gen * vSpacing
                    drawContext.canvas.nativeCanvas.drawText(
                        "Generation ${gen + 1}",
                        minX - 130f,
                        y + dateTextSize / 2f,
                        labelPaint
                    )
                }
            }

            // Spouse connectors: thick orange double line, edge to edge between the cards
            layout.couples.forEach { (a, b) ->
                val p1 = positions[a] ?: return@forEach
                val p2 = positions[b] ?: return@forEach
                val left = if (p1.x <= p2.x) p1 else p2
                val right = if (p1.x <= p2.x) p2 else p1
                val startX = left.x + cardWidth / 2
                val endX = right.x - cardWidth / 2
                val midY = (left.y + right.y) / 2
                drawLine(spouseColor, Offset(startX, midY - 3f), Offset(endX, midY - 3f), strokeWidth = 3f, cap = StrokeCap.Round)
                drawLine(spouseColor, Offset(startX, midY + 3f), Offset(endX, midY + 3f), strokeWidth = 3f, cap = StrokeCap.Round)
            }

            // Step/adopted sibling direct links
            layout.siblingLines.forEach { (a, b, cat) ->
                val p1 = positions[a] ?: return@forEach
                val p2 = positions[b] ?: return@forEach
                drawLine(bioColor, p1, p2, strokeWidth = 2.5f, pathEffect = connectorEffect(cat), cap = StrokeCap.Round)
            }

            // Parent -> children connectors. A vertical trunk drops from the center of the
            // couple (or from the single parent) to a horizontal bus that connects every
            // sibling, then a vertical branch rises into each child's card. No diagonals.
            layout.units.forEach { unit ->
                val partnerPositions = unit.partners.mapNotNull { positions[it] }
                if (partnerPositions.isEmpty() || unit.children.isEmpty()) return@forEach
                val childPositions = unit.children.mapNotNull { id -> positions[id]?.let { id to it } }
                if (childPositions.isEmpty()) return@forEach

                val trunkX = partnerPositions.map { it.x }.average().toFloat()
                val trunkBottomY = partnerPositions.maxOf { it.y } + cardHeight / 2f
                val childTopY = childPositions.minOf { it.second.y } - cardHeight / 2f
                val busY = (trunkBottomY + childTopY) / 2f
                val minX = minOf(trunkX, childPositions.minOf { it.second.x })
                val maxX = maxOf(trunkX, childPositions.maxOf { it.second.x })

                // Trunk from the parent(s) down to the sibling bus
                drawLine(bioColor, Offset(trunkX, trunkBottomY), Offset(trunkX, busY), strokeWidth = 2.5f)
                // Horizontal bus connecting all the siblings
                drawLine(bioColor, Offset(minX, busY), Offset(maxX, busY), strokeWidth = 2.5f)
                // Branch up into each child, styled by that child's relationship category
                childPositions.forEach { (childId, childPos) ->
                    val cat = layout.childCategory[childId] ?: RelCategory.BIO
                    drawLine(
                        bioColor,
                        Offset(childPos.x, busY),
                        Offset(childPos.x, childPos.y - cardHeight / 2f),
                        strokeWidth = 2.5f,
                        pathEffect = connectorEffect(cat)
                    )
                }
            }

            // Member cards on top
            members.forEach { member ->
                val pos = positions[member.id] ?: return@forEach
                drawMemberCard(
                    member = member,
                    center = pos,
                    cardWidth = cardWidth,
                    cardHeight = cardHeight,
                    avatarRadius = avatarRadius,
                    padding = cardPadding,
                    nameTextSize = nameTextSize,
                    dateTextSize = dateTextSize,
                    borderColor = personBorderColor(member.id, layout)
                )
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

        TreeLegend(
            modifier = Modifier
                .align(Alignment.TopStart)
                .padding(16.dp)
        )
    }
}

private fun DrawScope.drawMemberCard(
    member: FamilyMember,
    center: Offset,
    cardWidth: Float,
    cardHeight: Float,
    avatarRadius: Float,
    padding: Float,
    nameTextSize: Float,
    dateTextSize: Float,
    borderColor: Color
) {
    val left = center.x - cardWidth / 2
    val top = center.y - cardHeight / 2
    val cornerRadius = CornerRadius(14f, 14f)

    // Drop shadow
    drawRoundRect(
        color = Color(0x1A2E5C51),
        topLeft = Offset(left, top + 3f),
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

    // Subtle colored left border accent based on relationship type
    drawRoundRect(
        color = borderColor,
        topLeft = Offset(left, top),
        size = Size(6f, cardHeight),
        cornerRadius = CornerRadius(3f, 3f)
    )

    // Faint outer border
    drawRoundRect(
        color = Color(0xFFE7E9E4),
        topLeft = Offset(left, top),
        size = Size(cardWidth, cardHeight),
        cornerRadius = cornerRadius,
        style = Stroke(width = 1.2f)
    )

    // Avatar circle with initial
    val avatarCenter = Offset(left + padding + avatarRadius, center.y)
    drawCircle(color = borderColor.copy(alpha = 0.18f), radius = avatarRadius, center = avatarCenter)
    drawCircle(color = borderColor, radius = avatarRadius, center = avatarCenter, style = Stroke(width = 1.5f))

    val initial = member.first_name.trim().firstOrNull()?.uppercase() ?: "?"
    val avatarPaint = android.graphics.Paint().apply {
        color = android.graphics.Color.parseColor("#1C2826")
        textSize = avatarRadius
        textAlign = android.graphics.Paint.Align.CENTER
        typeface = android.graphics.Typeface.DEFAULT_BOLD
    }
    drawContext.canvas.nativeCanvas.drawText(
        initial,
        avatarCenter.x,
        avatarCenter.y + avatarRadius * 0.35f,
        avatarPaint
    )

    val textLeft = avatarCenter.x + avatarRadius + padding * 0.7f
    val textMaxWidth = (left + cardWidth - padding) - textLeft

    val namePaint = android.graphics.Paint().apply {
        color = android.graphics.Color.parseColor("#1C2826")
        textSize = nameTextSize
        textAlign = android.graphics.Paint.Align.LEFT
        typeface = android.graphics.Typeface.DEFAULT_BOLD
    }
    val datePaint = android.graphics.Paint().apply {
        color = android.graphics.Color.parseColor("#5A6B67")
        textSize = dateTextSize
        textAlign = android.graphics.Paint.Align.LEFT
        typeface = android.graphics.Typeface.DEFAULT
    }

    val fullName = listOf(member.first_name, member.last_name).filter { it.isNotBlank() }.joinToString(" ")
    val displayName = ellipsize(namePaint, fullName, textMaxWidth)
    val birthDate = member.birth_date?.takeIf { it.isNotBlank() }

    if (birthDate != null) {
        drawContext.canvas.nativeCanvas.drawText(displayName, textLeft, center.y - 2f, namePaint)
        drawContext.canvas.nativeCanvas.drawText(
            ellipsize(datePaint, birthDate, textMaxWidth),
            textLeft,
            center.y + dateTextSize + 6f,
            datePaint
        )
    } else {
        drawContext.canvas.nativeCanvas.drawText(displayName, textLeft, center.y + nameTextSize * 0.35f, namePaint)
    }
}

private fun ellipsize(paint: android.graphics.Paint, text: String, maxWidth: Float): String {
    if (maxWidth <= 0f || paint.measureText(text) <= maxWidth) return text
    val ellipsis = "…"
    val ellipsisWidth = paint.measureText(ellipsis)
    var count = paint.breakText(text, true, (maxWidth - ellipsisWidth).coerceAtLeast(0f), null)
    while (count > 0 && paint.measureText(text, 0, count) + ellipsisWidth > maxWidth) count--
    return text.substring(0, count) + ellipsis
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

@Composable
private fun TreeLegend(modifier: Modifier = Modifier) {
    Column(
        modifier = modifier
            .background(Color.White.copy(alpha = 0.92f), RoundedCornerShape(10.dp))
            .border(1.dp, Color(0xFF4A7C6F).copy(alpha = 0.25f), RoundedCornerShape(10.dp))
            .padding(horizontal = 12.dp, vertical = 10.dp)
    ) {
        LegendItem(label = "Spouse", color = Color(0xFFD4956A)) { color ->
            drawLine(color, Offset(0f, size.height / 2f - 3f), Offset(size.width, size.height / 2f - 3f), strokeWidth = 3f)
            drawLine(color, Offset(0f, size.height / 2f + 3f), Offset(size.width, size.height / 2f + 3f), strokeWidth = 3f)
        }
        Spacer(Modifier.height(8.dp))
        LegendItem(label = "Parent / Child", color = Color(0xFF4A7C6F)) { color ->
            drawLine(color, Offset(0f, size.height / 2f), Offset(size.width, size.height / 2f), strokeWidth = 3.5f)
        }
        Spacer(Modifier.height(8.dp))
        LegendItem(label = "Step", color = Color(0xFF4A7C6F)) { color ->
            drawLine(
                color, Offset(0f, size.height / 2f), Offset(size.width, size.height / 2f),
                strokeWidth = 3f, pathEffect = PathEffect.dashPathEffect(floatArrayOf(10f, 6f), 0f)
            )
        }
        Spacer(Modifier.height(8.dp))
        LegendItem(label = "Adopted", color = Color(0xFF4A7C6F)) { color ->
            drawLine(
                color, Offset(0f, size.height / 2f), Offset(size.width, size.height / 2f),
                strokeWidth = 3f, cap = StrokeCap.Round,
                pathEffect = PathEffect.dashPathEffect(floatArrayOf(1.5f, 6f), 0f)
            )
        }
    }
}

@Composable
private fun LegendItem(
    label: String,
    color: Color,
    drawIndicator: DrawScope.(Color) -> Unit
) {
    Row(verticalAlignment = Alignment.CenterVertically) {
        Canvas(modifier = Modifier.size(width = 28.dp, height = 14.dp)) {
            drawIndicator(color)
        }
        Spacer(Modifier.width(8.dp))
        Text(label, fontSize = 12.sp, color = Color(0xFF1C2826))
    }
}
