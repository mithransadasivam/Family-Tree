package com.familytree.familytree.ui.screens

import com.familytree.familytree.data.models.FamilyMember
import com.familytree.familytree.data.models.Relationship

// ---------------------------------------------------------------------------------------
// Generations: which row each person belongs on, worked out from the links ALONE.
//
// Every link pins generations down: a couple share one, a parent is above their child. Drawing by
// "how deep am I in the branch I was reached through" breaks whenever two branches disagree (a
// married-in spouse whose family is recorded deeper than their partner's). Solving for rows
// directly makes them a pure function of the relationships: the order people or links were
// entered in, and which family is drawn first, cannot change them. Same algorithm as the website
// (web/src/generations.ts).
//
// A tree can also hold links that cannot all be true together - typically one stored the wrong way
// round, e.g. Ann is Ben's father, Ben is Cara's father, and Ann and Cara are a couple. No rows
// satisfy that. drawableRelationships() finds such contradictions and sets aside the link most
// likely to be wrong (for drawing only; nothing is changed in the data) and says which.
// ---------------------------------------------------------------------------------------

/** A link left out of the drawing because it contradicts the others. */
internal class IgnoredLink(
    val id: Int,
    /** "Ann is the Mother of Ben": the way the stored link reads. */
    val reads: String,
    /** Why this one was chosen. */
    val why: String,
    /** The other links in the same conflict. Any one of them could be the one entered wrongly. */
    val alsoCheck: List<String> = emptyList()
)

/** (ancestor, descendant) for a link that makes member_1 a parent/child of member_2, else null. */
internal fun parentEdgeOf(rel: Relationship): Pair<Int, Int>? {
    val name = rel.relationship_type_name
    return when {
        name in bioParentTypes || name in stepParentTypes -> rel.member_1 to rel.member_2
        name in bioChildTypes || name in stepChildTypes || name in adoptedChildTypes -> rel.member_2 to rel.member_1
        else -> null
    }
}

private class Contracted(
    val find: (Int) -> Int,
    val out: Map<Int, Set<Int>>,
    val nodes: Set<Int>,
    /** Couple-nodes on a contradiction: a parent link back to themselves, or a loop of them. */
    val bad: Set<Int>,
    val scc: Map<Int, Int>
)

private fun contract(edges: List<Pair<Int, Int>>, couples: List<Pair<Int, Int>>, ids: Collection<Int>): Contracted {
    val parent = HashMap<Int, Int>()
    fun find(x: Int): Int {
        parent.putIfAbsent(x, x)
        var r = x
        while (parent[r] != r) r = parent[r]!!
        var c = x
        while (parent[c] != r) {
            val next = parent[c]!!
            parent[c] = r
            c = next
        }
        return r
    }
    couples.forEach { (a, b) -> parent[find(a)] = find(b) }
    val people = LinkedHashSet<Int>(ids)
    edges.forEach { (a, d) -> people += a; people += d }
    couples.forEach { (a, b) -> people += a; people += b }

    val nodes = LinkedHashSet<Int>()
    people.forEach { nodes += find(it) }
    val out = HashMap<Int, MutableSet<Int>>()
    val bad = HashSet<Int>()
    edges.forEach { (a, d) ->
        val ca = find(a)
        val cd = find(d)
        if (ca == cd) bad += ca else out.getOrPut(ca) { LinkedHashSet() } += cd
    }

    // Strongly connected components (Tarjan): any of 2+ nodes is a loop.
    val index = HashMap<Int, Int>()
    val low = HashMap<Int, Int>()
    val onStack = HashSet<Int>()
    val stack = ArrayList<Int>()
    val scc = HashMap<Int, Int>()
    var counter = 0
    fun visit(v: Int) {
        index[v] = counter
        low[v] = counter
        counter++
        stack += v
        onStack += v
        for (w in out[v].orEmpty()) {
            if (w !in index) {
                visit(w)
                low[v] = minOf(low[v]!!, low[w]!!)
            } else if (w in onStack) {
                low[v] = minOf(low[v]!!, index[w]!!)
            }
        }
        if (low[v] == index[v]) {
            val members = ArrayList<Int>()
            do {
                val w = stack.removeAt(stack.size - 1)
                onStack -= w
                members += w
            } while (w != v)
            members.forEach { scc[it] = v }
            if (members.size > 1) bad += members
        }
    }
    nodes.sorted().forEach { if (it !in index) visit(it) }
    return Contracted(::find, out, nodes, bad, scc)
}

private fun spouseCouples(relationships: List<Relationship>) =
    relationships.filter { it.relationship_type_name in spouseRelTypes }.map { it.member_1 to it.member_2 }

/** The parent links (ancestor, descendant) that sit on a contradiction about generations. */
internal fun generationConflictEdges(
    relationships: List<Relationship>,
    ids: Collection<Int> = emptyList()
): Set<Pair<Int, Int>> {
    val edges = relationships.mapNotNull { parentEdgeOf(it) }
    val c = contract(edges, spouseCouples(relationships), ids)
    return edges.filter { (a, d) ->
        val ca = c.find(a)
        val cd = c.find(d)
        ca == cd || (ca in c.bad && c.scc[ca] == c.scc[cd])
    }.toSet()
}

/**
 * Row (0 = top) for every person. Parents sit directly above their lowest child; couples share a
 * row; each separate family starts at 0. Only meaningful when nothing contradicts (see
 * drawableRelationships); people on a contradiction are left on row 0.
 */
internal fun assignGenerations(relationships: List<Relationship>, ids: Collection<Int>): Map<Int, Int> {
    val edges = relationships.mapNotNull { parentEdgeOf(it) }
    val c = contract(edges, spouseCouples(relationships), ids)
    val indeg = HashMap<Int, Int>()
    c.nodes.forEach { indeg[it] = 0 }
    c.out.values.forEach { kids -> kids.forEach { indeg[it] = (indeg[it] ?: 0) + 1 } }

    val order = ArrayList<Int>()
    val ready = ArrayDeque(c.nodes.filter { indeg[it] == 0 }.sorted())
    while (ready.isNotEmpty()) {
        val n = ready.removeFirst()
        order += n
        for (k in c.out[n].orEmpty()) {
            indeg[k] = indeg[k]!! - 1
            if (indeg[k] == 0) ready += k
        }
    }
    if (order.size != c.nodes.size) return ids.associateWith { 0 } // cyclic: caller should have repaired

    val gen = HashMap<Int, Int>()
    order.forEach { gen[it] = 0 }
    for (n in order) for (k in c.out[n].orEmpty()) gen[k] = maxOf(gen[k]!!, gen[n]!! + 1)
    // Pull parents down so each sits right above its nearest child instead of floating at the top.
    for (n in order.reversed()) {
        val kids = c.out[n]
        if (!kids.isNullOrEmpty()) gen[n] = kids.minOf { gen[it]!! - 1 }
    }

    // Each connected family starts at row 0.
    val cparent = HashMap<Int, Int>()
    fun cfind(x: Int): Int {
        var r = x
        while ((cparent[r] ?: r) != r) r = cparent[r]!!
        return r
    }
    c.out.forEach { (a, kids) -> kids.forEach { cparent[cfind(a)] = cfind(it) } }
    val min = HashMap<Int, Int>()
    c.nodes.forEach { n ->
        val r = cfind(n)
        min[r] = minOf(min[r] ?: Int.MAX_VALUE, gen[n]!!)
    }
    return ids.associateWith { id ->
        val n = c.find(id)
        gen[n]!! - min[cfind(n)]!!
    }
}

private fun nameOf(m: FamilyMember?, id: Int): String =
    m?.let { "${it.first_name} ${it.last_name}".trim() }?.takeIf { it.isNotEmpty() } ?: "#$id"

private fun readsOf(rel: Relationship, byId: Map<Int, FamilyMember>) =
    "${nameOf(byId[rel.member_1], rel.member_1)} is the ${rel.relationship_type_name} of " +
        nameOf(byId[rel.member_2], rel.member_2)

/** True when the link says member_1 is one gender but their profile records the other. */
private fun contradictsGender(rel: Relationship, byId: Map<Int, FamilyMember>): Boolean {
    val want = when (rel.relationship_type_name) {
        in maleTypes -> "male"
        in femaleTypes -> "female"
        else -> return false
    }
    val have = byId[rel.member_1]?.gender
    return (have == "male" || have == "female") && have != want
}

/**
 * The relationships to DRAW. If the links contradict each other about generations, set aside one
 * parent link at a time until the rest is consistent. The pick: a link that contradicts its
 * person's recorded gender first (the usual sign of one stored backwards); with no gender evidence,
 * the OLDEST link, because links saved by older app versions (before the direction fix of
 * 2026-11-04) are the ones known to be backwards. Ties fall to how the link reads, never to member
 * ids. Nothing is deleted or edited.
 */
internal fun drawableRelationships(
    members: List<FamilyMember>,
    relationships: List<Relationship>
): Pair<List<Relationship>, List<IgnoredLink>> {
    val byId = members.associateBy { it.id }
    val ids = members.map { it.id }
    val ignored = mutableListOf<IgnoredLink>()
    var kept = relationships
    repeat(relationships.size + 1) {
        val bad = generationConflictEdges(kept, ids)
        if (bad.isEmpty()) return kept to ignored
        val cands = kept
            .filter { r -> parentEdgeOf(r)?.let { it in bad } == true }
            .map { Triple(it, contradictsGender(it, byId), readsOf(it, byId)) }
            .sortedWith(
                compareByDescending<Triple<Relationship, Boolean, String>> { it.second }
                    .thenBy { it.first.id }
                    .thenBy { it.third }
            )
        val victim = cands.firstOrNull() ?: return kept to ignored
        ignored += IgnoredLink(
            victim.first.id,
            victim.third,
            if (victim.second) "the person's recorded gender does not match this link, so it was probably entered the wrong way round"
            else "it contradicts the other links and is the oldest of them, so it is the likeliest to have been entered the wrong way round",
            cands.drop(1).map { it.third }
        )
        kept = kept.filter { it !== victim.first }
    }
    return kept to ignored
}
