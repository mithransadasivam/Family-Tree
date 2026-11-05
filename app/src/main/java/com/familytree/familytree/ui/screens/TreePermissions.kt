package com.familytree.familytree.ui.screens

/**
 * Permission model: every tree member can add and edit people and relationships, but only the
 * tree owner can delete them (the backend enforces it; this keeps the UI honest).
 *
 * Anything unknown - still loading, or the lookup failed - counts as "not the owner", so the
 * delete actions are never shown on a guess.
 */
fun canDeleteInTree(meId: Int?, ownerId: Int?): Boolean =
    meId != null && ownerId != null && meId == ownerId
