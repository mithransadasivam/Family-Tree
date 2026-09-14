package com.familytree.familytree

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import com.familytree.familytree.ui.navigation.AppNavigation
import com.familytree.familytree.ui.theme.FamilyTreeTheme
import com.google.android.gms.ads.MobileAds

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        MobileAds.initialize(this) {}
        setContent {
            FamilyTreeTheme {
                AppNavigation()
            }
        }
    }
}
