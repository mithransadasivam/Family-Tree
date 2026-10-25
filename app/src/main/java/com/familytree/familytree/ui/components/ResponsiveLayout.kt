package com.familytree.familytree.ui.components

import androidx.compose.ui.Modifier
import androidx.compose.ui.layout.layout
import androidx.compose.ui.unit.Dp
import androidx.compose.ui.unit.dp

/** Widest a single column of content gets before it is centered instead of stretched (tablets, landscape). */
val MaxContentWidth = 640.dp

/**
 * Caps the width of the content at [max] and centers it horizontally within the available
 * space. On phones narrower than [max] this is a no-op; on tablets / landscape it stops
 * lists, cards and buttons from stretching edge to edge.
 */
fun Modifier.maxContentWidth(max: Dp = MaxContentWidth): Modifier = this.layout { measurable, constraints ->
    val width = minOf(constraints.maxWidth, max.roundToPx())
    val placeable = measurable.measure(
        constraints.copy(minWidth = minOf(constraints.minWidth, width), maxWidth = width)
    )
    layout(constraints.maxWidth, placeable.height) {
        placeable.placeRelative((constraints.maxWidth - placeable.width) / 2, 0)
    }
}
