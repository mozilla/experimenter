override fun toJson(): JsonObject {
    val obj = JSONObject(
        mapOf(
            "knownField" to knownField,
        ),
    )
    return obj
}
