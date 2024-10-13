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
import java.nio.ByteBuffer
import java.util.*


class MainActivity : ComponentActivity() {
    private lateinit var previewView: PreviewView
    private lateinit var imageView: ImageView
    private lateinit var cameraExecutor: ExecutorService
    private var isPermissionGranted = false
    private var imageCapture: ImageCapture? = null
    private var capturedImage: Bitmap? = null

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

                Log.d("takePhoto", "after setImage")

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

    override fun onDestroy() {
        super.onDestroy()
        cameraExecutor.shutdown() // Executor 종료
    }
}