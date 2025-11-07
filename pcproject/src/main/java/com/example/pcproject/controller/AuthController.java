package com.example.pcproject.controller;

import com.example.pcproject.domain.User;
import com.example.pcproject.service.UserService;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import jakarta.servlet.http.HttpSession;
import jakarta.servlet.http.HttpServletRequest;
import java.util.Map;

@RestController
@RequiredArgsConstructor
@RequestMapping("/api")
public class AuthController {

    private final UserService userService;

    // ✅ 회원가입
    @PostMapping("/register")
    public ResponseEntity<?> register(@RequestBody Map<String, String> req) {
        try {
            User user = userService.register(req.get("username"), req.get("name"), req.get("password"));
            return ResponseEntity.ok(Map.of(
                    "success", true,
                    "message", "회원가입 완료",
                    "user", Map.of(
                            "id", user.getId(),
                            "username", user.getUsername(),
                            "name", user.getName()
                    )
            ));
        } catch (Exception e) {
            return ResponseEntity.badRequest().body(Map.of(
                    "success", false,
                    "message", e.getMessage()
            ));
        }
    }

    // ✅ 로그인
    @PostMapping("/login")
    public ResponseEntity<?> login(@RequestBody Map<String, String> req,
                                   HttpSession session,
                                   HttpServletRequest request) {
        try {
            // ✅ 기존 세션 완전히 무효화
            if (session != null) {
                session.invalidate();
            }

            // ✅ 새 세션 발급
            session = request.getSession(true);

            User user = userService.login(req.get("username"), req.get("password"));

            // ✅ 새로운 세션에 사용자 ID 저장
            session.setAttribute("user_id", user.getId());

            // ✅ SecurityContext 등록 부분 그대로 유지
            org.springframework.security.core.userdetails.User authUser =
                    new org.springframework.security.core.userdetails.User(
                            user.getUsername(),
                            user.getPassword(),
                            new java.util.ArrayList<>()
                    );
            var authentication =
                    new org.springframework.security.authentication.UsernamePasswordAuthenticationToken(
                            authUser, null, authUser.getAuthorities());

            var context = org.springframework.security.core.context.SecurityContextHolder.createEmptyContext();
            context.setAuthentication(authentication);
            org.springframework.security.core.context.SecurityContextHolder.setContext(context);

            // ✅ SecurityContext를 세션에도 저장
            session.setAttribute(
                    org.springframework.security.web.context.HttpSessionSecurityContextRepository.SPRING_SECURITY_CONTEXT_KEY,
                    context
            );

            return ResponseEntity.ok(Map.of(
                    "success", true,
                    "message", "로그인 성공",
                    "user", Map.of(
                            "id", user.getId(),
                            "username", user.getUsername(),
                            "name", user.getName()
                    )
            ));
        } catch (Exception e) {
            return ResponseEntity.status(401).body(Map.of(
                    "success", false,
                    "message", e.getMessage()
            ));
        }
    }




    // ✅ 로그인 상태 확인
    @GetMapping("/auth/check")
    public ResponseEntity<?> checkLogin(HttpSession session) {
        Long userId = (Long) session.getAttribute("user_id");
        if (userId == null) {
            return ResponseEntity.ok(Map.of("loggedIn", false));
        }
        User user = userService.findById(userId)
                .orElse(null);
        if (user == null) {
            return ResponseEntity.ok(Map.of("loggedIn", false));
        }
        return ResponseEntity.ok(Map.of(
                "loggedIn", true,
                "user", Map.of(
                        "id", user.getId(),
                        "username", user.getUsername(), // admin
                        "name", user.getName()          // test
                )
        ));
    }


    // ✅ 로그아웃
    @PostMapping("/logout")
    public ResponseEntity<?> logout(HttpSession session) {
        session.invalidate(); // 세션 제거
        return ResponseEntity.ok(Map.of("success", true, "message", "로그아웃 완료"));
    }
}
