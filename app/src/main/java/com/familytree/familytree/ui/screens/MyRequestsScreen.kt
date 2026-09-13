package com.familytree.familytree.ui.screens

import androidx.compose.foundation.background
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
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.ArrowBack
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.CircularProgressIndicator
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
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.navigation.NavController
import com.familytree.familytree.data.models.JoinRequest
import com.familytree.familytree.data.repository.AppRepository
import com.familytree.familytree.ui.theme.Primary
import com.familytree.familytree.ui.theme.Surface
import com.familytree.familytree.ui.theme.TextHint
import com.familytree.familytree.ui.theme.TextPrimary

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun MyRequestsScreen(navController: NavController) {
    val context = LocalContext.current
    val repository = remember { AppRepository(context) }
    var myRequests by remember { mutableStateOf<List<JoinRequest>>(emptyList()) }
    var isLoading by remember { mutableStateOf(true) }

    LaunchedEffect(Unit) {
        val result = repository.getMyRequests()
        if (result.isSuccess) myRequests = result.getOrNull() ?: emptyList()
        isLoading = false
    }

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("My Join Requests", color = Color.White) },
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
        } else if (myRequests.isEmpty()) {
            Box(Modifier.fillMaxSize().padding(padding), contentAlignment = Alignment.Center) {
                Text("You haven't requested to join any trees", color = TextHint)
            }
        } else {
            LazyColumn(
                modifier = Modifier.fillMaxSize().padding(padding).padding(16.dp),
                verticalArrangement = Arrangement.spacedBy(12.dp)
            ) {
                items(myRequests, key = { it.id }) { req ->
                    Card(colors = CardDefaults.cardColors(containerColor = Surface)) {
                        Row(
                            modifier = Modifier.fillMaxWidth().padding(16.dp),
                            verticalAlignment = Alignment.CenterVertically
                        ) {
                            Column(Modifier.weight(1f)) {
                                Text(req.tree_name, fontWeight = FontWeight.Medium, color = TextPrimary)
                                if (req.message.isNotBlank()) {
                                    Spacer(Modifier.height(4.dp))
                                    Text(req.message, fontSize = 12.sp, color = TextHint)
                                }
                                Spacer(Modifier.height(4.dp))
                                Text(req.created_at.take(10), fontSize = 11.sp, color = TextHint)
                            }
                            Spacer(Modifier.width(8.dp))
                            StatusBadge(req.status)
                        }
                    }
                }
            }
        }
    }
}

@Composable
private fun StatusBadge(status: String) {
    val (bg, fg, label) = when (status) {
        "approved" -> Triple(Color(0xFFDDF3E4), Color(0xFF2E7D5B), "Approved")
        "rejected" -> Triple(Color(0xFFFBE2E1), Color(0xFFC0392B), "Rejected")
        else -> Triple(Color(0xFFFDF3D8), Color(0xFFB8860B), "Pending")
    }
    Box(
        modifier = Modifier
            .background(bg, RoundedCornerShape(50))
            .padding(horizontal = 10.dp, vertical = 4.dp)
    ) {
        Text(label, color = fg, fontSize = 12.sp, fontWeight = FontWeight.Medium)
    }
}
