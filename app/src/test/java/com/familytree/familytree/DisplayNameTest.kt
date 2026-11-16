package com.familytree.familytree

import com.familytree.familytree.data.models.FamilyMember
import com.familytree.familytree.data.models.displayName
import org.junit.Assert.assertEquals
import org.junit.Test

class DisplayNameTest {
    private fun m(first: String, last: String) = FamilyMember(
        id = 1, tree = 1, user = null, first_name = first, last_name = last, phone = "", email = "",
        address = "", photo_url = "", birth_date = null, birth_place = "", death_date = null,
        death_place = "", gender = null, created_at = "", updated_at = "",
    )

    @Test fun fullNameWhenThereIsALastName() = assertEquals("Thalapathy Vijay", m("Thalapathy", "Vijay").displayName())
    @Test fun firstNameAloneWithoutALastName() = assertEquals("Deepa", m("Deepa", "").displayName())
    @Test fun blankLastNameDoesNotLeaveTrailingSpace() = assertEquals("Deepa", m("Deepa", "  ").displayName())
}
