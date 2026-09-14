package com.familytree.familytree.data.api

import android.content.Context
import androidx.datastore.preferences.core.stringPreferencesKey
import androidx.datastore.preferences.preferencesDataStore
import com.familytree.familytree.BuildConfig
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.runBlocking
import okhttp3.Interceptor
import okhttp3.OkHttpClient
import okhttp3.logging.HttpLoggingInterceptor
import retrofit2.Retrofit
import retrofit2.converter.gson.GsonConverterFactory

val Context.dataStore by preferencesDataStore(name = "auth")

object TokenManager {
    val TOKEN_KEY = stringPreferencesKey("access_token")

    fun getToken(context: Context): String? {
        return runBlocking {
            context.dataStore.data.first()[TOKEN_KEY]
        }
    }
}

object RetrofitClient {
    private const val BASE_URL = "https://family-tree-backend-production.up.railway.app/api/"

    fun create(context: Context): ApiService {
        val authInterceptor = Interceptor { chain ->
            val token = TokenManager.getToken(context)
            val request = if (token != null) {
                chain.request().newBuilder()
                    .addHeader("Authorization", "Bearer $token")
                    .build()
            } else {
                chain.request()
            }
            chain.proceed(request)
        }

        val clientBuilder = OkHttpClient.Builder().addInterceptor(authInterceptor)

        // Full request/response bodies (auth headers, emails, phone numbers, birth dates)
        // must never be written to Logcat in a release build - only attach the logging
        // interceptor for debug builds.
        if (BuildConfig.DEBUG) {
            val logging = HttpLoggingInterceptor().apply {
                level = HttpLoggingInterceptor.Level.BODY
            }
            clientBuilder.addInterceptor(logging)
        }

        val client = clientBuilder.build()

        return Retrofit.Builder()
            .baseUrl(BASE_URL)
            .client(client)
            .addConverterFactory(GsonConverterFactory.create())
            .build()
            .create(ApiService::class.java)
    }
}
