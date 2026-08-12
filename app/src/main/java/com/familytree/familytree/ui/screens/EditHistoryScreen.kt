package com.familytree.familytree.ui.screens

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxHeight
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.ArrowBack
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.Divider
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.material3.TopAppBar
import androidx.compose.material3.TopAppBarDefaults
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.navigation.NavController
import com.familytree.familytree.data.models.EditHistory
import com.familytree.familytree.data.repository.AppRepository
import com.familytree.familytree.ui.theme.Primary
import com.familytree.familytree.ui.theme.TextHint

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun EditHistoryScreen(navController: NavController, treeId: Int) {
    val context = LocalContext.current
    val repository = remember { AppRepository(context) }
    var history by remember { mutableStateOf<List<EditHistory>>(emptyList()) }
    var isLoading by remember { mutableStateOf(true) }

    LaunchedEffect(treeId) {
        val result = repository.getEditHistory(treeId)
        if (result.isSuccess) history = result.getOrNull() ?: emptyList()
        isLoading = false
    }

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("Edit History", color = Color.White) },
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
                verticalArrangement = Arrangement.spacedBy(10.dp)
            ) {
                items(history) { item ->
                    Row(
                        modifier = Modifier.fillMaxWidth()
                    ) {
                        Box(
                            modifier = Modifier.width(3.dp).height(50.dp),
                            contentAlignment = Alignment.TopStart
                        ) {
                            Divider(
                                color = Primary,
                                modifier = Modifier.fillMaxHeight().width(3.dp)
                            )
                        }
                        Spacer(Modifier.width(12.dp))
                        Column {
                            Text(item.change_description, fontSize = 13.sp)
                            Text(
                                "${item.edited_by.first_name} · ${item.edited_at.take(10)}",
                                fontSize = 11.sp,
                                color = TextHint
                            )
                        }
                    }
                }
            }
        }
    }
}
