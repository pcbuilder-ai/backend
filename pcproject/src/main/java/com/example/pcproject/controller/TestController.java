package com.example.pcproject.controller;

import com.example.pcproject.domain.User;
import com.example.pcproject.service.UserService;
import com.example.pcproject.service.AiService;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.*;
import org.springframework.http.ResponseEntity;
import java.util.Map;
import java.util.HashMap;

@RestController
@RequiredArgsConstructor
@CrossOrigin(
    originPatterns = "*",
    allowedHeaders = "*",
    methods = {RequestMethod.GET, RequestMethod.POST, RequestMethod.PUT, RequestMethod.DELETE, RequestMethod.OPTIONS},
    allowCredentials = "true"
)
public class TestController {

    private final UserService userService;
    private final AiService aiService;

    // 인증 없이 접근 가능
    @GetMapping("/")
    public String home() {
        return "여기는 홈 페이지입니다. (인증 불필요)";
    }

    // 로그인해야 접근 가능
    @GetMapping("/secure")
    public String securePage() {
        return "로그인 성공! 이 페이지는 인증된 사용자만 볼 수 있습니다. (인증 필요)";
    }

    // 로그인 API
    @PostMapping(value = "/api/login", produces = "application/json; charset=UTF-8", consumes = "application/json; charset=UTF-8")
    public ResponseEntity<Map<String, Object>> login(@RequestBody Map<String, String> loginRequest) {
        String username = loginRequest.get("username");
        String password = loginRequest.get("password");
        
        Map<String, Object> response = new HashMap<>();
        
        try {
            // DB에서 사용자 인증
            User user = userService.login(username, password);
            
            // 성공 응답
            Map<String, Object> userData = new HashMap<>();
            userData.put("username", user.getUsername());
            userData.put("name", user.getName());
            userData.put("role", user.getRole());
            
            Map<String, Object> data = new HashMap<>();
            data.put("success", true);
            data.put("message", "로그인 성공");
            data.put("user", userData);
            
            response.put("success", true);
            response.put("data", data);
            return ResponseEntity.ok(response);
            
        } catch (IllegalArgumentException e) {
            // 로그인 실패
            Map<String, Object> data = new HashMap<>();
            data.put("success", false);
            data.put("message", e.getMessage());
            
            response.put("success", false);
            response.put("data", data);
            return ResponseEntity.status(401).body(response);
            
        } catch (Exception e) {
            // 기타 에러
            Map<String, Object> data = new HashMap<>();
            data.put("success", false);
            data.put("message", "로그인 중 오류가 발생했습니다.");
            
            response.put("success", false);
            response.put("data", data);
            return ResponseEntity.status(500).body(response);
        }
    }

    // 사용자 정보 조회 API
    @GetMapping("/api/user")
    public ResponseEntity<Map<String, Object>> getUserInfo() {
        Map<String, Object> response = new HashMap<>();
        response.put("success", true);
        response.put("user", Map.of("username", "testuser", "role", "ROLE_USER"));
        return ResponseEntity.ok(response);
    }

    // 회원가입 API
    @PostMapping(value = "/api/register", produces = "application/json; charset=UTF-8", consumes = "application/json; charset=UTF-8")
    public ResponseEntity<Map<String, Object>> register(@RequestBody Map<String, String> registerRequest) {
        String username = registerRequest.get("username");
        String name = registerRequest.get("name");
        String password = registerRequest.get("password");
        
        Map<String, Object> response = new HashMap<>();
        
        try {
            // 회원가입 처리
            User newUser = userService.register(username, name, password);
            
            // 성공 응답
            Map<String, Object> userData = new HashMap<>();
            userData.put("username", newUser.getUsername());
            userData.put("name", newUser.getName());
            userData.put("role", newUser.getRole());
            
            Map<String, Object> data = new HashMap<>();
            data.put("success", true);
            data.put("message", "회원가입이 완료되었습니다.");
            data.put("user", userData);
            
            response.put("success", true);
            response.put("data", data);
            return ResponseEntity.ok(response);
            
        } catch (IllegalArgumentException e) {
            // 중복 아이디 등의 에러
            Map<String, Object> data = new HashMap<>();
            data.put("success", false);
            data.put("message", e.getMessage());
            
            response.put("success", false);
            response.put("data", data);
            return ResponseEntity.status(400).body(response);
            
        } catch (Exception e) {
            // 기타 에러
            Map<String, Object> data = new HashMap<>();
            data.put("success", false);
            data.put("message", "회원가입 중 오류가 발생했습니다.");
            
            response.put("success", false);
            response.put("data", data);
            return ResponseEntity.status(500).body(response);
        }
    }

    // 채팅 API (OpenAI Chat Completions 형태 요청을 그대로 전달)
    @PostMapping("/api/chat")
    public ResponseEntity<Map<String, Object>> chat(@RequestBody Map<String, Object> chatRequest) {
        try {
            @SuppressWarnings("unchecked")
            var messages = (java.util.List<java.util.Map<String, String>>) chatRequest.get("messages");
            String model = chatRequest.getOrDefault("model", "gpt-4o-mini").toString();
            Integer maxTokens = chatRequest.get("max_tokens") instanceof Number ? ((Number) chatRequest.get("max_tokens")).intValue() : null;
            Double temperature = chatRequest.get("temperature") instanceof Number ? ((Number) chatRequest.get("temperature")).doubleValue() : null;

            Map<String, Object> result = aiService.chat(messages, model, maxTokens, temperature);
            return ResponseEntity.ok(result);
        } catch (Exception e) {
            Map<String, Object> error = new HashMap<>();
            error.put("success", false);
            error.put("message", "AI 처리 중 오류가 발생했습니다.");
            error.put("detail", e.getMessage());
            return ResponseEntity.status(500).body(error);
        }
    }

}