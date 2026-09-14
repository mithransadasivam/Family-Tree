package com.familytree.familytree.ui.screens

import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.horizontalScroll
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
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.ArrowBack
import androidx.compose.material.icons.filled.DateRange
import androidx.compose.material.icons.filled.Delete
import androidx.compose.material.icons.filled.Edit
import androidx.compose.material.icons.filled.Search
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.DatePicker
import androidx.compose.material3.DatePickerDialog
import androidx.compose.material3.Divider
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.FilterChip
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.ModalBottomSheet
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.RadioButton
import androidx.compose.material3.Scaffold
import androidx.compose.material3.SnackbarHost
import androidx.compose.material3.SnackbarHostState
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.material3.TopAppBar
import androidx.compose.material3.TopAppBarDefaults
import androidx.compose.material3.rememberDatePickerState
import androidx.compose.material3.rememberModalBottomSheetState
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
import com.familytree.familytree.ui.components.BannerAd
import com.familytree.familytree.ui.theme.Primary
import com.familytree.familytree.ui.theme.Surface
import com.familytree.familytree.ui.theme.TextHint
import kotlinx.coroutines.launch
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale
import java.util.TimeZone

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
    var relLanguage by remember { mutableStateOf(RelationshipLanguage.ENGLISH) }
    var relSearchQuery by remember { mutableStateOf("") }
    var selectedTerm by remember { mutableStateOf<RelationshipTerm?>(null) }
    var collapsedCategories by remember { mutableStateOf<Set<RelationshipCategory>>(emptySet()) }
    var editingRelationshipId by remember { mutableStateOf<Int?>(null) }

    var showEditSheet by remember { mutableStateOf(false) }
    var editFirstName by remember { mutableStateOf("") }
    var editLastName by remember { mutableStateOf("") }
    var editPhone by remember { mutableStateOf("") }
    var editEmail by remember { mutableStateOf("") }
    var editBirthDate by remember { mutableStateOf("") }
    var editBirthPlace by remember { mutableStateOf("") }
    var editDeathDate by remember { mutableStateOf("") }
    var editDeathPlace by remember { mutableStateOf("") }
    var isSavingEdit by remember { mutableStateOf(false) }
    var editError by remember { mutableStateOf("") }
    var showDeleteMemberConfirm by remember { mutableStateOf(false) }
    var relationshipPendingDelete by remember { mutableStateOf<Relationship?>(null) }
    val snackbarHostState = remember { SnackbarHostState() }

    fun openEditSheet(m: FamilyMember) {
        editFirstName = m.first_name
        editLastName = m.last_name
        editPhone = m.phone
        editEmail = m.email
        editBirthDate = m.birth_date ?: ""
        editBirthPlace = m.birth_place
        editDeathDate = m.death_date ?: ""
        editDeathPlace = m.death_place
        editError = ""
        showEditSheet = true
    }

    fun openAddRelSheet() {
        selectedMemberId = 0
        relLanguage = RelationshipLanguage.ENGLISH
        relSearchQuery = ""
        collapsedCategories = emptySet()
        selectedTerm = null
        editingRelationshipId = null
        showAddRel = true
    }

    fun openEditRelSheet(rel: Relationship) {
        selectedMemberId = if (rel.member_1 == memberId) rel.member_2 else rel.member_1
        relLanguage = RelationshipLanguage.ENGLISH
        relSearchQuery = ""
        collapsedCategories = emptySet()
        selectedTerm = findEnglishTerm(rel.relationship_type_name)
        editingRelationshipId = rel.id
        showAddRel = true
    }

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
        snackbarHost = { SnackbarHost(snackbarHostState) },
        topBar = {
            TopAppBar(
                title = { Text(member?.first_name ?: "Member", color = Color.White) },
                navigationIcon = {
                    IconButton(onClick = { navController.popBackStack() }) {
                        Icon(Icons.Filled.ArrowBack, contentDescription = "Back", tint = Color.White)
                    }
                },
                actions = {
                    IconButton(onClick = { member?.let { openEditSheet(it) } }) {
                        Icon(Icons.Filled.Edit, contentDescription = "Edit", tint = Color.White)
                    }
                    IconButton(onClick = { showDeleteMemberConfirm = true }) {
                        Icon(Icons.Filled.Delete, contentDescription = "Delete", tint = Color.White)
                    }
                },
                colors = TopAppBarDefaults.topAppBarColors(containerColor = Primary)
            )
        },
        bottomBar = { BannerAd(modifier = Modifier.fillMaxWidth()) }
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
                                if (m.death_date != null) {
                                    Row(Modifier.padding(vertical = 8.dp)) {
                                        Text("🕊 ", fontSize = 16.sp)
                                        Column {
                                            Text("Death Date", fontSize = 11.sp, color = TextHint)
                                            Text(m.death_date)
                                        }
                                    }
                                }
                                if (m.death_place.isNotEmpty()) {
                                    Row(Modifier.padding(vertical = 8.dp)) {
                                        Text("📍 ", fontSize = 16.sp)
                                        Column {
                                            Text("Death Place", fontSize = 11.sp, color = TextHint)
                                            Text(m.death_place)
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
                                IconButton(onClick = { openEditRelSheet(rel) }) {
                                    Icon(Icons.Default.Edit, contentDescription = "Edit relationship", tint = Primary)
                                }
                                IconButton(onClick = { relationshipPendingDelete = rel }) {
                                    Icon(Icons.Default.Delete, contentDescription = "Delete relationship", tint = Color.Red.copy(alpha = 0.7f))
                                }
                            }
                        }
                    }
                    item {
                        OutlinedButton(
                            onClick = { openAddRelSheet() },
                            modifier = Modifier.fillMaxWidth()
                        ) { Text("+ Add Relationship") }
                    }
                }
            }
        }
    }

    if (showAddRel && allMembers.isNotEmpty() && relTypes.isNotEmpty()) {
        if (selectedMemberId == 0) selectedMemberId = allMembers.first().id
        val selectedOther = allMembers.find { it.id == selectedMemberId }

        fun closeAddRel() {
            showAddRel = false
            selectedTerm = null
            relSearchQuery = ""
            relLanguage = RelationshipLanguage.ENGLISH
            editingRelationshipId = null
        }

        val visibleTerms = remember(relLanguage, relSearchQuery) {
            termsForLanguage(relLanguage).filter {
                relSearchQuery.isBlank() || it.label.contains(relSearchQuery, ignoreCase = true)
            }
        }
        val groupedTerms = remember(visibleTerms) {
            RelationshipCategory.entries
                .associateWith { cat -> visibleTerms.filter { it.category == cat } }
                .filterValues { it.isNotEmpty() }
        }

        val sheetState = rememberModalBottomSheetState(skipPartiallyExpanded = true)
        ModalBottomSheet(
            onDismissRequest = { closeAddRel() },
            sheetState = sheetState
        ) {
            Column(modifier = Modifier.fillMaxSize().padding(horizontal = 20.dp)) {
                Text(
                    if (editingRelationshipId != null) "Edit Relationship" else "Add Relationship",
                    fontSize = 18.sp,
                    fontWeight = FontWeight.Medium
                )
                Spacer(Modifier.height(12.dp))

                // Sentence preview
                Card(
                    colors = CardDefaults.cardColors(containerColor = Color(0xFFE8F4F1)),
                    modifier = Modifier.fillMaxWidth()
                ) {
                    Text(
                        text = "${member?.first_name} is the ${selectedTerm?.label ?: "..."} of ${selectedOther?.first_name ?: "..."}",
                        modifier = Modifier.padding(12.dp),
                        fontSize = 14.sp,
                        color = Color(0xFF2E5C51),
                        fontWeight = FontWeight.Medium
                    )
                }
                Spacer(Modifier.height(16.dp))

                Text("Select Other Member", fontSize = 12.sp, color = TextHint)
                Spacer(Modifier.height(4.dp))
                Box(
                    modifier = Modifier
                        .heightIn(max = 130.dp)
                        .verticalScroll(rememberScrollState())
                ) {
                    Column {
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
                    }
                }

                Spacer(Modifier.height(16.dp))
                Text("Relationship Type", fontSize = 12.sp, color = TextHint)
                Spacer(Modifier.height(8.dp))

                // Step 1 - language/culture chips
                Row(
                    modifier = Modifier
                        .fillMaxWidth()
                        .horizontalScroll(rememberScrollState()),
                    horizontalArrangement = Arrangement.spacedBy(8.dp)
                ) {
                    RelationshipLanguage.entries.forEach { lang ->
                        FilterChip(
                            selected = relLanguage == lang,
                            onClick = {
                                relLanguage = lang
                                // Keep the current pick if it still exists in this language's
                                // list (e.g. a basic English term shared across languages);
                                // otherwise it wouldn't be visible/selectable anymore, so drop it.
                                if (selectedTerm != null && selectedTerm !in termsForLanguage(lang)) {
                                    selectedTerm = null
                                }
                            },
                            label = { Text("${lang.emoji} ${lang.label}") }
                        )
                    }
                }
                Spacer(Modifier.height(10.dp))

                // Step 2 - search
                OutlinedTextField(
                    value = relSearchQuery,
                    onValueChange = { relSearchQuery = it },
                    placeholder = { Text("Search relationship...") },
                    leadingIcon = { Icon(Icons.Filled.Search, contentDescription = null) },
                    singleLine = true,
                    modifier = Modifier.fillMaxWidth()
                )
                Spacer(Modifier.height(4.dp))

                // Step 3 - categorized, collapsible list. Category order (RelationshipCategory.entries)
                // and each term's position within its category (language terms first, then the
                // shared English basics - see termsForLanguage) never change based on selection or
                // search, only on which items are present - so switching languages/searching only
                // adds or removes rows in place rather than reshuffling everything. Every row keeps
                // a stable key and animates into its new position/fades in-or-out via animateItem()
                // instead of the list jumping straight to its new layout.
                LazyColumn(modifier = Modifier.weight(1f).fillMaxWidth()) {
                    if (groupedTerms.isEmpty()) {
                        item(key = "no_matches") {
                            Text(
                                "No matches found",
                                color = TextHint,
                                modifier = Modifier.padding(vertical = 16.dp).animateItem()
                            )
                        }
                    }
                    groupedTerms.forEach { (category, terms) ->
                        val isExpanded = category !in collapsedCategories
                        item(key = "header_${category.name}") {
                            Column(modifier = Modifier.animateItem()) {
                                Row(
                                    modifier = Modifier
                                        .fillMaxWidth()
                                        .clickable {
                                            collapsedCategories = if (isExpanded) {
                                                collapsedCategories + category
                                            } else {
                                                collapsedCategories - category
                                            }
                                        }
                                        .padding(vertical = 10.dp),
                                    verticalAlignment = Alignment.CenterVertically
                                ) {
                                    Text(
                                        "${category.emoji} ${category.label}",
                                        fontWeight = FontWeight.Medium,
                                        fontSize = 14.sp,
                                        modifier = Modifier.weight(1f)
                                    )
                                    Text(if (isExpanded) "▾" else "▸", color = TextHint)
                                }
                                Divider(color = Color(0x1A4A7C6F))
                            }
                        }
                        if (isExpanded) {
                            items(terms, key = { "${category.name}_${it.label}" }) { term ->
                                val isSelected = selectedTerm == term
                                Row(
                                    modifier = Modifier
                                        .fillMaxWidth()
                                        .animateItem()
                                        .clickable { selectedTerm = term }
                                        .background(if (isSelected) Color(0xFFE8F4F1) else Color.Transparent)
                                        .padding(vertical = 8.dp),
                                    verticalAlignment = Alignment.CenterVertically
                                ) {
                                    RadioButton(selected = isSelected, onClick = { selectedTerm = term })
                                    Column {
                                        Text(term.label, fontSize = 14.sp)
                                        if (term.englishType != term.label) {
                                            Text(term.englishType, fontSize = 11.sp, color = TextHint)
                                        }
                                    }
                                }
                            }
                        }
                    }
                }

                Spacer(Modifier.height(8.dp))
                Row(
                    modifier = Modifier.fillMaxWidth().padding(bottom = 20.dp),
                    horizontalArrangement = Arrangement.End
                ) {
                    TextButton(onClick = { closeAddRel() }) { Text("Cancel") }
                    Spacer(Modifier.width(8.dp))
                    Button(
                        onClick = {
                            val term = selectedTerm ?: return@Button
                            val relType = relTypes.find { it.type_name == term.englishType }
                            if (relType == null) {
                                scope.launch { snackbarHostState.showSnackbar("This relationship type isn't available right now") }
                                return@Button
                            }
                            val relIdBeingEdited = editingRelationshipId
                            scope.launch {
                                member?.let { m ->
                                    // When editing, delete the old relationship first, then create the
                                    // replacement. If the delete fails, bail out before touching
                                    // anything so the original relationship is left intact. If the
                                    // delete succeeds but the create fails, the list is still
                                    // refreshed and the user is told - so the UI never quietly shows
                                    // stale data as if the edit had worked.
                                    if (relIdBeingEdited != null) {
                                        val deleteResult = repository.deleteRelationship(relIdBeingEdited)
                                        if (!deleteResult.isSuccess) {
                                            snackbarHostState.showSnackbar(deleteResult.exceptionOrNull()?.message ?: "Failed to update relationship")
                                            return@launch
                                        }
                                    }
                                    val createResult = repository.createRelationship(
                                        CreateRelationshipRequest(
                                            tree = m.tree,
                                            member_1 = m.id,
                                            member_2 = selectedMemberId,
                                            relationship_type = relType.id
                                        )
                                    )
                                    val relsResult = repository.getRelationships(m.tree)
                                    if (relsResult.isSuccess) relationships = relsResult.getOrNull()
                                        ?.filter { it.member_1 == memberId || it.member_2 == memberId }
                                        ?: emptyList()
                                    closeAddRel()
                                    if (createResult.isSuccess) {
                                        snackbarHostState.showSnackbar(if (relIdBeingEdited != null) "Relationship updated" else "Relationship added")
                                    } else {
                                        snackbarHostState.showSnackbar(createResult.exceptionOrNull()?.message ?: "Failed to save relationship")
                                    }
                                }
                            }
                        },
                        enabled = selectedTerm != null
                    ) { Text(if (editingRelationshipId != null) "Save" else "Add") }
                }
            }
        }
    }

    if (showEditSheet) {
        val sheetState = rememberModalBottomSheetState(skipPartiallyExpanded = true)
        ModalBottomSheet(
            onDismissRequest = { if (!isSavingEdit) showEditSheet = false },
            sheetState = sheetState
        ) {
            Column(
                modifier = Modifier
                    .fillMaxWidth()
                    .verticalScroll(rememberScrollState())
                    .padding(horizontal = 20.dp)
                    .padding(bottom = 24.dp)
            ) {
                Text("Edit Member", fontSize = 18.sp, fontWeight = FontWeight.Medium)
                Spacer(Modifier.height(16.dp))
                OutlinedTextField(value = editFirstName, onValueChange = { editFirstName = it }, label = { Text("First Name") }, modifier = Modifier.fillMaxWidth(), enabled = !isSavingEdit)
                Spacer(Modifier.height(8.dp))
                OutlinedTextField(value = editLastName, onValueChange = { editLastName = it }, label = { Text("Last Name") }, modifier = Modifier.fillMaxWidth(), enabled = !isSavingEdit)
                Spacer(Modifier.height(8.dp))
                OutlinedTextField(value = editPhone, onValueChange = { editPhone = it }, label = { Text("Phone") }, modifier = Modifier.fillMaxWidth(), enabled = !isSavingEdit)
                Spacer(Modifier.height(8.dp))
                OutlinedTextField(value = editEmail, onValueChange = { editEmail = it }, label = { Text("Email") }, modifier = Modifier.fillMaxWidth(), enabled = !isSavingEdit)
                Spacer(Modifier.height(8.dp))
                EditDateField(label = "Birth Date", value = editBirthDate, enabled = !isSavingEdit, onValueChange = { editBirthDate = it })
                Spacer(Modifier.height(8.dp))
                OutlinedTextField(value = editBirthPlace, onValueChange = { editBirthPlace = it }, label = { Text("Birth Place") }, modifier = Modifier.fillMaxWidth(), enabled = !isSavingEdit)
                Spacer(Modifier.height(8.dp))
                EditDateField(label = "Death Date (optional)", value = editDeathDate, enabled = !isSavingEdit, onValueChange = { editDeathDate = it })
                Spacer(Modifier.height(8.dp))
                OutlinedTextField(value = editDeathPlace, onValueChange = { editDeathPlace = it }, label = { Text("Death Place (optional)") }, modifier = Modifier.fillMaxWidth(), enabled = !isSavingEdit)

                if (editError.isNotEmpty()) {
                    Spacer(Modifier.height(12.dp))
                    Text(editError, color = MaterialTheme.colorScheme.error, fontSize = 13.sp)
                }

                Spacer(Modifier.height(20.dp))
                Button(
                    onClick = {
                        editError = ""
                        isSavingEdit = true
                        scope.launch {
                            val updates = mutableMapOf(
                                "first_name" to editFirstName,
                                "last_name" to editLastName,
                                "phone" to editPhone,
                                "email" to editEmail,
                                "birth_place" to editBirthPlace,
                                "death_place" to editDeathPlace
                            )
                            if (editBirthDate.isNotBlank()) updates["birth_date"] = editBirthDate
                            if (editDeathDate.isNotBlank()) updates["death_date"] = editDeathDate
                            val result = repository.updateFamilyMember(memberId, updates)
                            isSavingEdit = false
                            if (result.isSuccess) {
                                member = result.getOrNull()
                                showEditSheet = false
                                snackbarHostState.showSnackbar("Member updated successfully")
                            } else {
                                editError = result.exceptionOrNull()?.message ?: "Failed to update member"
                            }
                        }
                    },
                    enabled = !isSavingEdit && editFirstName.isNotBlank(),
                    modifier = Modifier.fillMaxWidth()
                ) {
                    if (isSavingEdit) {
                        CircularProgressIndicator(color = Color.White, modifier = Modifier.size(20.dp))
                    } else {
                        Text("Save")
                    }
                }
            }
        }
    }

    if (showDeleteMemberConfirm) {
        AlertDialog(
            onDismissRequest = { showDeleteMemberConfirm = false },
            title = { Text("Delete Member") },
            text = { Text("Are you sure you want to delete ${member?.first_name ?: "this member"}? This action cannot be undone.") },
            confirmButton = {
                Button(
                    onClick = {
                        showDeleteMemberConfirm = false
                        scope.launch {
                            member?.let { m ->
                                val result = repository.deleteFamilyMember(m.id)
                                if (result.isSuccess) {
                                    navController.popBackStack()
                                } else {
                                    snackbarHostState.showSnackbar(result.exceptionOrNull()?.message ?: "Failed to delete member")
                                }
                            }
                        }
                    },
                    colors = ButtonDefaults.buttonColors(containerColor = Color.Red)
                ) { Text("Delete") }
            },
            dismissButton = { TextButton(onClick = { showDeleteMemberConfirm = false }) { Text("Cancel") } }
        )
    }

    relationshipPendingDelete?.let { relToDelete ->
        AlertDialog(
            onDismissRequest = { relationshipPendingDelete = null },
            title = { Text("Delete Relationship") },
            text = { Text("Are you sure you want to remove this relationship?") },
            confirmButton = {
                Button(
                    onClick = {
                        relationshipPendingDelete = null
                        scope.launch {
                            val result = repository.deleteRelationship(relToDelete.id)
                            if (result.isSuccess) {
                                member?.let { m ->
                                    val relsResult = repository.getRelationships(m.tree)
                                    if (relsResult.isSuccess) relationships = relsResult.getOrNull()
                                        ?.filter { it.member_1 == memberId || it.member_2 == memberId }
                                        ?: emptyList()
                                }
                            } else {
                                snackbarHostState.showSnackbar(result.exceptionOrNull()?.message ?: "Failed to delete relationship")
                            }
                        }
                    },
                    colors = ButtonDefaults.buttonColors(containerColor = Color.Red)
                ) { Text("Delete") }
            },
            dismissButton = { TextButton(onClick = { relationshipPendingDelete = null }) { Text("Cancel") } }
        )
    }
}

@Composable
private fun EditDateField(label: String, value: String, enabled: Boolean, onValueChange: (String) -> Unit) {
    var showPicker by remember { mutableStateOf(false) }
    OutlinedTextField(
        value = value,
        onValueChange = {},
        label = { Text(label) },
        modifier = Modifier.fillMaxWidth(),
        enabled = enabled,
        readOnly = true,
        trailingIcon = {
            IconButton(onClick = { if (enabled) showPicker = true }) {
                Icon(Icons.Filled.DateRange, contentDescription = "Pick date")
            }
        }
    )
    if (showPicker) {
        val datePickerState = rememberDatePickerState(
            initialSelectedDateMillis = value.takeIf { it.isNotBlank() }?.let { parseIsoDateToMillis(it) }
        )
        DatePickerDialog(
            onDismissRequest = { showPicker = false },
            confirmButton = {
                TextButton(onClick = {
                    datePickerState.selectedDateMillis?.let { millis -> onValueChange(formatMillisToIsoDate(millis)) }
                    showPicker = false
                }) { Text("OK") }
            },
            dismissButton = {
                TextButton(onClick = { showPicker = false }) { Text("Cancel") }
            }
        ) {
            DatePicker(state = datePickerState)
        }
    }
}

private fun isoDateFormat(): SimpleDateFormat {
    return SimpleDateFormat("yyyy-MM-dd", Locale.US).apply {
        timeZone = TimeZone.getTimeZone("UTC")
    }
}

private fun parseIsoDateToMillis(dateStr: String): Long? {
    return try { isoDateFormat().parse(dateStr)?.time } catch (e: Exception) { null }
}

private fun formatMillisToIsoDate(millis: Long): String = isoDateFormat().format(Date(millis))
