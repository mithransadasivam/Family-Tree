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
import com.familytree.familytree.data.api.AuthConfig
import com.familytree.familytree.data.repository.AppRepository
import com.familytree.familytree.ui.navigation.Screen
import com.familytree.familytree.ui.theme.*
import com.google.android.gms.auth.api.signin.GoogleSignIn
import com.google.android.gms.auth.api.signin.GoogleSignInOptions
import com.google.android.gms.auth.api.signin.GoogleSignInStatusCodes
import com.google.android.gms.common.api.ApiException
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext

@Composable
fun LoginScreen(navController: NavController) {
    val context = LocalContext.current
    val scope = rememberCoroutineScope()
    val repository = remember { AppRepository(context) }
    var isLoading by remember { mutableStateOf(false) }
    var checkingSession by remember { mutableStateOf(true) }
    var errorMessage by remember { mutableStateOf("") }

    // A saved token from a previous session should skip straight to Home instead of forcing
    // the user to tap "Continue with Google" again every time the app is relaunched. The check
    // itself reads DataStore synchronously (via runBlocking under the hood), so it's pushed off
    // the main thread here rather than run directly inside the composable.
    LaunchedEffect(Unit) {
        val loggedIn = withContext(Dispatchers.IO) { repository.isLoggedIn() }
        if (loggedIn) {
            navController.navigate(Screen.Home.route) {
                popUpTo(Screen.Login.route) { inclusive = true }
            }
        } else {
            checkingSession = false
        }
    }

    val gso = GoogleSignInOptions.Builder(GoogleSignInOptions.DEFAULT_SIGN_IN)
        .requestIdToken(AuthConfig.GOOGLE_WEB_CLIENT_ID)
        .requestEmail()
        .build()

    val googleSignInClient = remember { GoogleSignIn.getClient(context, gso) }

    val launcher = rememberLauncherForActivityResult(
        contract = ActivityResultContracts.StartActivityForResult()
    ) { result ->
        Log.d(
            "GoogleSignIn",
            "Result code: ${result.resultCode} (RESULT_OK=${Activity.RESULT_OK}, RESULT_CANCELED=${Activity.RESULT_CANCELED}), " +
                "data extras: ${result.data?.extras}"
        )
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
                            val ex = authResult.exceptionOrNull()
                            Log.e("GoogleSignIn", "Backend auth failed", ex)
                            errorMessage = "Backend login failed: ${ex?.message ?: "unknown error"}"
                        }
                    }
                } else {
                    errorMessage = "Signed in to Google but no ID token was returned. Check that the Web Client ID matches an OAuth client of type 'Web application' in the same GCP project as the Android client."
                }
            } catch (e: ApiException) {
                val statusText = GoogleSignInStatusCodes.getStatusCodeString(e.statusCode)
                Log.e("GoogleSignIn", "ApiException status code: ${e.statusCode} ($statusText)", e)
                errorMessage = "Google sign in failed: $statusText (code ${e.statusCode})"
            }
        } else {
            Log.e(
                "GoogleSignIn",
                "Sign-in flow returned resultCode=${result.resultCode} instead of RESULT_OK. " +
                    "This is commonly caused by: (1) the debug keystore's SHA-1 not being registered " +
                    "on an Android OAuth client in Google Cloud Console for package com.familytree.familytree, " +
                    "(2) the OAuth consent screen being in Testing mode without this Google account added as a " +
                    "test user, or (3) no Google account configured on the device/emulator."
            )
            errorMessage = "Google sign-in was cancelled or failed (code: ${result.resultCode}, expected ${Activity.RESULT_OK}). " +
                "Check Logcat tag 'GoogleSignIn' for details — likely an unregistered SHA-1 or OAuth consent screen issue in Google Cloud Console."
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
            if (isLoading || checkingSession) {
                CircularProgressIndicator(color = Primary)
            } else {
                Button(
                    onClick = { launcher.launch(googleSignInClient.signInIntent) },
                    modifier = Modifier.fillMaxWidth().height(50.dp),
                    colors = ButtonDefaults.buttonColors(containerColor = Primary)
                ) {
                    Text("Continue with Google", color = androidx.compose.ui.graphics.Color.White)
                }
            }
        }
    }
}
