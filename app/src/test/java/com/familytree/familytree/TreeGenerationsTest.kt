package com.familytree.familytree

import com.familytree.familytree.data.models.FamilyMember
import com.familytree.familytree.data.models.Relationship
import com.familytree.familytree.ui.screens.assignGenerations
import com.familytree.familytree.ui.screens.buildTreeLayout
import com.familytree.familytree.ui.screens.drawableRelationships
import com.familytree.familytree.ui.screens.generationConflictEdges
import com.familytree.familytree.ui.screens.parentEdgeOf
import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test
import java.util.Random

/**
 * The layout puts people on rows worked out from the links alone, and says so when links
 * contradict each other. Mirrors web/src/generations.test.tsx.
 *
 * The real family: "Siva Sankar". Row 134 was stored the wrong way round by an old Android build
 * ("Sivasankaran is the Mother of Jayalakshmi"). No parent loop exists on its own, because the
 * spouse link is not a parent link, yet it makes Jayalakshmi both Sivananthan's partner and his
 * grandchild's ancestor.
 */
class TreeGenerationsTest {
    private var relId = 1000
    private fun person(id: Int, first: String, gender: String? = null) = FamilyMember(
        id = id, tree = 1, user = null, first_name = first, last_name = "", phone = "", email = "",
        address = "", photo_url = "", birth_date = null, birth_place = "", death_date = null,
        death_place = "", gender = gender, created_at = "", updated_at = ""
    )

    private fun rel(a: Int, type: String, b: Int) =
        Relationship(relId++, 1, a, b, 0, type, "", "")

    private data class Edge(val a: String, val type: String, val b: String)

    private class Built(val members: List<FamilyMember>, val rels: List<Relationship>)

    /** Row of each person BY NAME after the real layout. */
    private fun rowsByName(members: List<FamilyMember>, rels: List<Relationship>): Map<String, Int> {
        val layout = layoutOf(members, rels)
        val names = members.associate { it.id to it.first_name }
        return layout.genOfPerson.mapKeys { names.getValue(it.key) }
    }

    private fun layoutOf(members: List<FamilyMember>, rels: List<Relationship>) =
        buildTreeLayout(members, rels, members.associate { it.id to 200f }, 20f, 20f, 160f, 140f, 90f)

    private fun <T> permutations(xs: List<T>): List<List<T>> =
        if (xs.size <= 1) listOf(xs)
        else xs.indices.flatMap { i -> permutations(xs.take(i) + xs.drop(i + 1)).map { listOf(xs[i]) + it } }

    private val roles = listOf("Sivananthan", "Jayalakshmi", "Sivasankaran", "Amutha", "Pooja", "Teja", "Inbashri")
    private val genderOf = mapOf("Sivananthan" to "male", "Jayalakshmi" to "female", "Sivasankaran" to "male", "Amutha" to "female")
    private val common = listOf(
        Edge("Sivasankaran", "Son", "Sivananthan"), // row 140
        Edge("Pooja", "Daughter", "Sivasankaran"), Edge("Teja", "Daughter", "Sivasankaran"),
        Edge("Inbashri", "Daughter", "Sivasankaran"),
        Edge("Amutha", "Spouse", "Sivasankaran"), Edge("Sivananthan", "Spouse", "Jayalakshmi")
    )
    private val backwards = listOf(Edge("Sivasankaran", "Mother", "Jayalakshmi"))
    private val correct = listOf(Edge("Jayalakshmi", "Mother", "Sivasankaran"))
    private val expected = mapOf(
        "Sivananthan" to 0, "Jayalakshmi" to 0, "Sivasankaran" to 1, "Amutha" to 1,
        "Pooja" to 2, "Teja" to 2, "Inbashri" to 2
    )

    private fun build(ids: List<Int>, extra: List<Edge>): Built {
        fun id(n: String) = ids[roles.indexOf(n)]
        val members = roles.map { person(id(it), it, genderOf[it]) }.sortedBy { it.id }
        return Built(members, (common + extra).map { rel(id(it.a), it.type, id(it.b)) })
    }

    @Test
    fun reportedFamilyDrawsTheSameCorrectRowsForEveryOrderPeopleWereAdded() {
        for (ids in permutations((1..7).toList())) {
            val b = build(ids, backwards)
            assertEquals("ids $ids", expected, rowsByName(b.members, b.rels))
        }
    }

    @Test
    fun theBackwardsLinkIsNamedAndLeftOutOfTheDrawing() {
        val b = build((1..7).toList(), backwards)
        val layout = layoutOf(b.members, b.rels)
        assertEquals(listOf("Sivasankaran is the Mother of Jayalakshmi"), layout.ignoredLinks.map { it.reads })
        assertTrue(layout.ignoredLinks.single().why.contains("gender"))
    }

    @Test
    fun theSameLinkEnteredCorrectlyReportsNothing() {
        val b = build((1..7).toList(), correct)
        val layout = layoutOf(b.members, b.rels)
        assertTrue(layout.ignoredLinks.isEmpty())
        assertEquals(expected, rowsByName(b.members, b.rels))
    }

    @Test
    fun productionShapeWithNoGendersSetsAsideTheOlderLinkAndDrawsTheFamilyRightWayUp() {
        // Real ids from the "Siva sankar" tree: nobody has a gender, and row 134 (old Android build)
        // is older than row 140.
        val ms = listOf(
            person(44, "Sivasankaran S"), person(45, "Amutha Siva"), person(50, "Jayalakshmi"),
            person(58, "Sivananthan"), person(60, "Pooja"), person(61, "Teja"), person(62, "Inba")
        )
        fun r(id: Int, a: Int, t: String, b: Int) = Relationship(id, 13, a, b, 0, t, "", "")
        val rels = listOf(
            r(91, 45, "Spouse", 44), r(94, 62, "Daughter", 44), r(95, 61, "Daughter", 44), r(96, 60, "Daughter", 44),
            r(132, 58, "Spouse", 50), r(134, 44, "Mother", 50), r(140, 44, "Son", 58)
        )
        for (order in listOf(rels, rels.reversed())) {
            val layout = layoutOf(ms, order)
            assertEquals(listOf(134), layout.ignoredLinks.map { it.id })
            assertEquals(listOf("Sivasankaran S is the Son of Sivananthan"), layout.ignoredLinks.single().alsoCheck)
            assertEquals(
                mapOf("Sivananthan" to 0, "Jayalakshmi" to 0, "Sivasankaran S" to 1, "Amutha Siva" to 1,
                    "Pooja" to 2, "Teja" to 2, "Inba" to 2),
                rowsByName(ms, order)
            )
        }
    }

    @Test
    fun theStoredRelationshipsAreNotTouched() {
        val b = build((1..7).toList(), backwards)
        val before = b.rels.map { Triple(it.id, it.member_1, it.member_2) }
        layoutOf(b.members, b.rels)
        assertEquals(before, b.rels.map { Triple(it.id, it.member_1, it.member_2) })
    }

    @Test
    fun aContradictionThatOnlyShowsUpThroughACoupleIsDetected() {
        val edges = generationConflictEdges(listOf(rel(1, "Husband", 2), rel(1, "Father", 3), rel(3, "Father", 2)))
        assertEquals(setOf(1 to 3, 3 to 2), edges)
    }

    @Test
    fun aPlainParentLoopIsDetected() {
        val edges = generationConflictEdges(listOf(rel(1, "Father", 2), rel(2, "Father", 3), rel(3, "Father", 1)))
        assertEquals(3, edges.size)
    }

    @Test
    fun aNormalFamilyAndAMarriageBetweenLineagesAreNotFlagged() {
        val rels = listOf(
            rel(1, "Husband", 2), rel(1, "Father", 3), rel(2, "Mother", 3),
            rel(3, "Husband", 4), rel(5, "Father", 4)
        )
        assertTrue(generationConflictEdges(rels).isEmpty())
    }

    @Test
    fun generationsArePureAndParentsSitDirectlyAboveTheirLowestChild() {
        val rels = listOf(rel(1, "Husband", 2), rel(1, "Father", 3), rel(3, "Husband", 4), rel(5, "Father", 4), rel(6, "Father", 5))
        assertEquals(
            mapOf(1 to 1, 2 to 1, 3 to 2, 4 to 2, 5 to 1, 6 to 0),
            assignGenerations(rels, listOf(1, 2, 3, 4, 5, 6))
        )
    }

    @Test
    fun aContradictionIsBrokenTheSameWayWhateverTheOrderAndWithoutGenders() {
        val members = (1..3).map { person(it, "n$it") }
        val rels = listOf(rel(1, "Father", 2), rel(2, "Father", 3), rel(3, "Father", 1))
        val a = drawableRelationships(members, rels)
        val b = drawableRelationships(members.reversed(), rels.reversed())
        assertEquals(a.second.map { it.reads }, b.second.map { it.reads })
        assertEquals(1, a.second.size)
        assertTrue(generationConflictEdges(a.first).isEmpty())
    }

    // -----------------------------------------------------------------------------------
    // Random families: rows must satisfy every link, cards must not overlap, and nothing may
    // depend on ids or on the order links arrive in.
    // -----------------------------------------------------------------------------------
    private class Family(val names: List<String>, val edges: List<Edge>)

    private fun family(seed: Int): Family {
        val r = Random(seed.toLong())
        fun <T> pick(xs: List<T>) = xs[r.nextInt(xs.size)]
        val names = mutableListOf<String>()
        val edges = mutableListOf<Edge>()
        val gen = List(4) { mutableListOf<String>() }
        fun make(g: Int): String { val n = "p${names.size}"; names += n; gen[g] += n; return n }
        repeat(1 + r.nextInt(2)) { make(0) }
        for (g in 0 until 3) {
            for (p in gen[g].toList()) {
                if (r.nextDouble() < 0.75) {
                    val mates = mutableListOf<String>()
                    repeat(if (r.nextDouble() < 0.2) 2 else 1) {
                        val sp = make(g); mates += sp; edges += Edge(p, pick(listOf("Husband", "Wife", "Spouse")), sp)
                    }
                    repeat(r.nextInt(3)) {
                        val c = make(g + 1)
                        val flip = r.nextDouble() < 0.4
                        val parents = if (r.nextDouble() < 0.8) listOf(p, mates[0]) else listOf(p)
                        for (par in parents) edges += if (flip) Edge(c, pick(listOf("Son", "Daughter")), par)
                        else Edge(par, pick(listOf("Father", "Mother")), c)
                    }
                }
            }
        }
        for (n in names.toList()) { // married-in people sometimes have their own recorded parents
            if (r.nextDouble() < 0.25 && edges.none { it.type in setOf("Father", "Mother") && it.b == n }) {
                val pa = "q${names.size}"; names += pa; edges += Edge(pa, "Father", n)
            }
        }
        if (r.nextDouble() < 0.3 && gen[2].isNotEmpty()) edges += Edge(gen[0][0], "Grandfather", gen[2][0])
        return Family(names, edges)
    }

    private fun instance(f: Family, ids: List<Int>, order: List<Edge>): Built {
        fun id(n: String) = ids[f.names.indexOf(n)]
        return Built(
            f.names.mapIndexed { i, n -> person(ids[i], n) }.sortedBy { it.id },
            order.map { rel(id(it.a), it.type, id(it.b)) }
        )
    }

    @Test
    fun randomFamiliesPutEveryParentAboveTheirChildWithNoOverlappingCards() {
        for (seed in 1..1500) {
            val f = family(seed)
            val b = instance(f, f.names.indices.map { it + 1 }, f.edges)
            val layout = layoutOf(b.members, b.rels)
            assertTrue("seed $seed is consistent", layout.ignoredLinks.isEmpty())
            for (rel in b.rels) {
                val (anc, desc) = parentEdgeOf(rel) ?: continue
                assertTrue("seed $seed: $anc above $desc", layout.genOfPerson.getValue(desc) > layout.genOfPerson.getValue(anc))
            }
            assertEquals("seed $seed: everyone is placed once", b.members.size, layout.positions.size)
            layout.positions.entries.groupBy { it.value.y }.values.forEach { row ->
                val xs = row.map { it.value.x }.sorted()
                for (i in 1 until xs.size) assertTrue("seed $seed: cards overlap", xs[i] - xs[i - 1] >= 200f - 0.01f)
            }
        }
    }

    @Test
    fun randomFamiliesDrawTheSameRowsHoweverIdsAndLinksAreOrdered() {
        for (seed in 1..400) {
            val f = family(seed)
            val r = Random(seed * 7919L)
            val base = instance(f, f.names.indices.map { it + 1 }, f.edges)
            val want = rowsByName(base.members, base.rels)
            repeat(3) {
                val ids = f.names.indices.map { it + 1 }.shuffled(r)
                val other = instance(f, ids, f.edges.shuffled(r))
                assertEquals("seed $seed", want, rowsByName(other.members, other.rels))
            }
        }
    }
}
