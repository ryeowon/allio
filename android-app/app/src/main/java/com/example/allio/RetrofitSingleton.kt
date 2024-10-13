import com.example.allio.MainActivity
import retrofit2.Retrofit
import retrofit2.converter.gson.GsonConverterFactory

object RetrofitSingleton {
    private const val BASE_URL = "http://192.168.219.108:5001/" // Flask

    private val retrofit: Retrofit by lazy {
        Retrofit.Builder()
            .baseUrl(BASE_URL)
            .addConverterFactory(GsonConverterFactory.create())
            .build()
    }

    val apiService: MainActivity.ApiService by lazy {
        retrofit.create(MainActivity.ApiService::class.java)
    }
}