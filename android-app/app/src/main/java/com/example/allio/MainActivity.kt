package com.example.allio

import android.Manifest
import android.content.pm.PackageManager
import android.graphics.Bitmap
import android.os.Bundle
import android.widget.Button
import android.widget.Toast
import androidx.activity.ComponentActivity
import androidx.camera.core.Preview
import androidx.core.app.ActivityCompat
import androidx.core.content.ContextCompat
import androidx.camera.core.*
import androidx.camera.lifecycle.ProcessCameraProvider
import androidx.camera.view.PreviewView
import java.util.concurrent.ExecutorService
import androidx.camera.core.CameraSelector
import androidx.camera.core.ImageCapture
import androidx.camera.core.ImageCaptureException
import android.graphics.BitmapFactory
import android.graphics.Matrix
import android.util.Log
import android.widget.ImageView
import java.io.ByteArrayOutputStream
import java.nio.ByteBuffer
import android.util.Base64
import okhttp3.ResponseBody
import retrofit2.Call
import retrofit2.Callback
import retrofit2.Response
import retrofit2.Retrofit
import retrofit2.converter.gson.GsonConverterFactory
import retrofit2.http.Body
import retrofit2.http.POST


class MainActivity : ComponentActivity() {
    private lateinit var previewView: PreviewView
    private lateinit var imageView: ImageView
    private lateinit var cameraExecutor: ExecutorService
    private var isPermissionGranted = false
    private var imageCapture: ImageCapture? = null
    private var capturedImage: Bitmap? = null

    data class ClaudeRequest(
        val image: String
    )

    // API 인터페이스 정의
    interface ApiService {
        @POST("claude") // 엔드포인트 정의
        fun getDescription(@Body request: ClaudeRequest): Call<ResponseBody> // 응답으로 ResponseBody를 받을 예정
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)
        previewView = findViewById(R.id.previewView)
        imageView = findViewById(R.id.imageView)
        var captureButton = findViewById<Button>(R.id.captureButton)

        checkPermission()

        if (isPermissionGranted) {
            startCamera()

            captureButton.setOnClickListener {
                takePhoto()
            }
        }
    }
    private fun checkPermission() {
        val permissionCheck = ContextCompat.checkSelfPermission(
            this, Manifest.permission.CAMERA
        )

        if (permissionCheck != PackageManager.PERMISSION_GRANTED) {
            ActivityCompat.requestPermissions(
                this, arrayOf<String>(Manifest.permission.CAMERA),
                1000
            )
            Toast.makeText(
                this@MainActivity, "카메라 권한이 필요합니다.",
                Toast.LENGTH_SHORT
            ).show()
            return
        } else {
            isPermissionGranted = true
        }
    }

    private fun startCamera() {
        val cameraProviderFuture = ProcessCameraProvider.getInstance(this)

        cameraProviderFuture.addListener({
            val cameraProvider = cameraProviderFuture.get()
            val preview = Preview.Builder().build().also {
                it.setSurfaceProvider(previewView.surfaceProvider)
            }

            // 카메라 선택 (뒤쪽 카메라)
            val cameraSelector = CameraSelector.DEFAULT_BACK_CAMERA

            // ImageCapture 객체 생성
            imageCapture = ImageCapture.Builder().build()

            // 카메라 바인딩
            try {
                cameraProvider.unbindAll() // 이전 바인딩 해제
                cameraProvider.bindToLifecycle(this, cameraSelector, preview, imageCapture)
            } catch (exc: Exception) {
                Toast.makeText(this, "카메라 시작 실패: ${exc.message}", Toast.LENGTH_SHORT).show()
            }
        }, ContextCompat.getMainExecutor(this))
    }

    private fun takePhoto() {
        Log.d("takePhoto", imageCapture.toString())
        val imageCapture = imageCapture ?: return
        imageCapture.takePicture(ContextCompat.getMainExecutor(this), object : ImageCapture.OnImageCapturedCallback() {
            override fun onCaptureSuccess(imageProxy: ImageProxy) {

                val rotationDegrees = imageProxy.imageInfo.rotationDegrees

                // ImageProxy를 Bitmap으로 변환
                val bitmap = imageProxyToBitmap(imageProxy)
                // 이미지 회전 처리
                val rotatedBitmap = rotateBitmap(bitmap, rotationDegrees)
                capturedImage = rotatedBitmap

                // 이미지 표시
                imageView.setImageBitmap(capturedImage)

                // 이미지 전송
                callApi(rotatedBitmap)

                // ImageProxy는 사용 후 닫아야 함
                imageProxy.close()
            }

            override fun onError(exception: ImageCaptureException) {
                Log.e("CameraXApp", "사진 캡처 실패: ${exception.message}", exception)
            }
        })
    }

    private fun imageProxyToBitmap(imageProxy: ImageProxy): Bitmap {
        val buffer: ByteBuffer = imageProxy.planes[0].buffer
        val bytes = ByteArray(buffer.remaining())
        buffer.get(bytes)
        return BitmapFactory.decodeByteArray(bytes, 0, bytes.size)
    }

    // 비트맵 회전 함수
    private fun rotateBitmap(bitmap: Bitmap, rotationDegrees: Int): Bitmap {
        val matrix = Matrix()
        matrix.postRotate(rotationDegrees.toFloat())
        return Bitmap.createBitmap(bitmap, 0, 0, bitmap.width, bitmap.height, matrix, true)
    }

    fun compressBitmapToBase64(bitmap: Bitmap, maxFileSize: Int = 4 * 1024 * 1024): String {
        val outputStream = ByteArrayOutputStream()

        var compressQuality = 100  // 시작 압축률 (100% = 압축 안 함)
        var byteArray: ByteArray

        // 이미지를 압축하면서 크기를 줄임
        do {
            outputStream.reset()  // 스트림을 초기화하여 이전 압축 데이터를 삭제
            bitmap.compress(Bitmap.CompressFormat.JPEG, compressQuality, outputStream)
            byteArray = outputStream.toByteArray()
            compressQuality -= 5  // 압축률을 점차 높임 (5%씩 감소)
        } while (byteArray.size > maxFileSize && compressQuality > 0)

        // 압축된 이미지를 Base64 문자열로 변환
        return Base64.encodeToString(byteArray, Base64.NO_WRAP)
    }

    fun callApi(bitmap: Bitmap) {
        // Bitmap을 Base64로 인코딩
        val base64Image = compressBitmapToBase64(bitmap)

        // 요청 데이터 생성
        val uploadRequest = ClaudeRequest(image = base64Image)

        // API 호출
        RetrofitSingleton.apiService.getDescription(uploadRequest).enqueue(object : Callback<ResponseBody> {
            override fun onResponse(call: Call<ResponseBody>, response: Response<ResponseBody>) {
                if (response.isSuccessful) {
                    val responseData = response.body()?.string()
                    // 응답 처리 (UI 업데이트 등)
                    if (responseData != null) {
                        Log.d("callApi", responseData)
                    }
                } else {
                    // 오류 처리
                    Log.d("callApi", "Error: ${response.message()}")
                }
            }

            override fun onFailure(call: Call<ResponseBody>, t: Throwable) {
                t.printStackTrace()
                // 실패 처리 (UI 업데이트 등)
            }
        })
    }

    override fun onDestroy() {
        super.onDestroy()
        cameraExecutor.shutdown() // Executor 종료
    }
}