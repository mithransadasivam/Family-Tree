package com.familytree.familytree.ui.components

import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.viewinterop.AndroidView
import com.google.android.gms.ads.AdRequest
import com.google.android.gms.ads.AdSize
import com.google.android.gms.ads.AdView

@Composable
fun BannerAd(modifier: Modifier = Modifier) {
    AndroidView(
        modifier = modifier,
        factory = { context ->
            AdView(context).apply {
                setAdSize(AdSize.BANNER)
                adUnitId = "ca-app-pub-1067859484205439/8693686656"
                loadAd(AdRequest.Builder().build())
            }
        },
        // AdView owns a WebView-backed rendering surface that isn't freed automatically when
        // the composable leaves composition (e.g. navigating away) - destroy() releases it.
        onRelease = { it.destroy() }
    )
}
