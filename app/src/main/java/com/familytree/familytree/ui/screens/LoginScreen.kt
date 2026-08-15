package com.familytree.familytree.ui.screens

import android.app.Activity
import android.util.Log
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.navigation.NavController
import com.familytree.familytree.data.repository.AppRepository
import com.familytree.familytree.ui.navigation.Screen
import com.familytree.familytree.ui.theme.*
import com.google.android.gms.auth.api.signin.GoogleSignIn
import com.google.android.gms.auth.api.signin.GoogleSignInOptions
import com.google.android.gms.common.api.ApiException
import kotlinx.coroutines.launch

@Composable
fun LoginScreen(navController: NavController) {
    val context = LocalContext.current
    val scope = rememberCoroutineScope()
    val repository = remember { AppRepository(context) }
    var isLoading by remember { mutableStateOf(false) }
    var errorMessage by remember { mutableStateOf("") }

    val gso = GoogleSignInOptions.Builder(GoogleSignInOptions.DEFAULT_SIGN_IN)
        .requestIdToken("274201294258-7sd4aqc4m7vm54avvas15ir20c7aq4gn.apps.googleusercontent.com")
        .requestEmail()
        .build()

    val googleSignInClient = remember { GoogleSignIn.getClient(context, gso) }

    val launcher = rememberLauncherForActivityResult(
        contract = ActivityResultContracts.StartActivityForResult()
    ) { result ->
        Log.d("GoogleSignIn", "Result code: ${result.resultCode}")
        if (result.resultCode == Activity.RESULT_OK) {
            val task = GoogleSignIn.getSignedInAccountFromIntent(result.data)
            try {
                val account = task.getResult(ApiException::class.java)
                val idToken = account.idToken
                Log.d("GoogleSignIn", "Got account: ${account.email}, token null: ${idToken == null}")
                if (idToken != null) {
                    isLoading = true
                    scope.launch {
                        val authResult = repository.googleAuth(idToken)
                        isLoading = false
                        if (authResult.isSuccess) {
                            navController.navigate(Screen.Home.route) {
                                popUpTo(Screen.Login.route) { inclusive = true }
                            }
                        } else {
                            errorMessage = authResult.exceptionOrNull()?.message ?: "Login failed"
                        }
                    }
                } else {
                    errorMessage = "Could not get ID token from Google"
                }
            } catch (e: ApiException) {
                Log.e("GoogleSignIn", "ApiException status code: ${e.statusCode}")
                errorMessage = "Google sign in failed: code ${e.statusCode}"
            }
        } else {
            errorMessage = "Sign in cancelled or failed (code: ${result.resultCode})"
        }
    }

    Box(
        modifier = Modifier.fillMaxSize(),
        contentAlignment = Alignment.Center
    ) {
        Column(
            modifier = Modifier.fillMaxWidth().padding(32.dp),
            horizontalAlignment = Alignment.CenterHorizontally,
            verticalArrangement = Arrangement.Center
        ) {
            Text("🌳", fontSize = 64.sp)
            Spacer(modifier = Modifier.height(16.dp))
            Text("Family Tree", fontSize = 28.sp, fontWeight = FontWeight.Light, color = TextPrimary)
            Text("Connect your roots", fontSize = 14.sp, color = TextHint)
            Spacer(modifier = Modifier.height(48.dp))
            if (errorMessage.isNotEmpty()) {
                Card(
                    colors = CardDefaults.cardColors(containerColor = androidx.compose.ui.graphics.Color(0xFFFFEEEE))
                ) {
                    Text(errorMessage, color = MaterialTheme.colorScheme.error, modifier = Modifier.padding(12.dp))
                }
                Spacer(modifier = Modifier.height(16.dp))
            }
            if (isLoading) {
                CircularProgressIndicator(color = Primary)
            } else {
                Button(
                    onClick = { launcher.launch(googleSignInClient.signInIntent) },
                    modifier = Modifier.fillMaxWidth().height(50.dp),
                    colors = ButtonDefaults.buttonColors(containerColor = Primary)
                ) {
                    Text("Continue with Google", color = androidx.compose.ui.graphics.Color.White)
                }
                Spacer(modifier = Modifier.height(12.dp))
                OutlinedButton(
                    onClick = {
                        isLoading = true
                        scope.launch {
                            repository.saveToken("eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzg3MzY1MjkyLCJpYXQiOjE3ODY3NjA0OTIsImp0aSI6Ijc5ZjBkN2ZiODJhYzRhOTE5MjIyNGMxZjhkZTFiNjFkIiwidXNlcl9pZCI6MSwiZW1haWwiOiJ0ZXN0QGZhbWlseS5jb20ifQ.TcvU14C1nJoWHE0PGGnOl3kmhMMmodBSVIckEfay-zM")
                            isLoading = false
                            navController.navigate(Screen.Home.route) {
                                popUpTo(Screen.Login.route) { inclusive = true }
                            }
                        }
                    },
                    modifier = Modifier.fillMaxWidth().height(50.dp)
                ) {
                    Text("Dev Login (Testing Only)", color = Primary)
                }
            }
        }
    }
}
