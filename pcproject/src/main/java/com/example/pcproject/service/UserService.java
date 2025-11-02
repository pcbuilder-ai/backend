package com.example.pcproject.service;

import com.example.pcproject.domain.User;
import com.example.pcproject.repository.UserRepository;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;

import jakarta.annotation.PostConstruct;
import lombok.RequiredArgsConstructor;

import java.io.BufferedWriter;
import java.io.FileWriter;
import java.io.IOException;
import java.nio.file.Paths;

@Service
@RequiredArgsConstructor
public class UserService {

    private final UserRepository userRepository;
    private final PasswordEncoder passwordEncoder;
    
    private static final String USER_DATA_FILE = "backend/user_data.txt";

    // 애플리케이션 시작 시 DB에 'testuser' 계정(PW: 1234)을 생성
    @PostConstruct
    public void init() {
        if (userRepository.findByUsername("testuser").isEmpty()) {
            User testUser = User.builder()
                    .username("testuser")
                    .name("테스트유저")
                    // 비밀번호는 반드시 인코딩해야 합니다!
                    .password(passwordEncoder.encode("1234"))
                    .build();
            userRepository.save(testUser);
            System.out.println("--- [TEST] 초기 사용자 'testuser' 생성 완료 (PW: 1234) ---");
        }
    }

    // 로그인 (사용자 인증)
    public User login(String username, String password) {
        // DB에서 사용자 조회
        User user = userRepository.findByUsername(username)
                .orElseThrow(() -> new IllegalArgumentException("아이디 또는 비밀번호가 올바르지 않습니다."));

        // 비밀번호 검증
        if (!passwordEncoder.matches(password, user.getPassword())) {
            throw new IllegalArgumentException("아이디 또는 비밀번호가 올바르지 않습니다.");
        }

        return user;
    }

    // 회원가입
    public User register(String username, String name, String password) {
        // 이미 존재하는 사용자인지 확인
        if (userRepository.findByUsername(username).isPresent()) {
            throw new IllegalArgumentException("이미 사용 중인 아이디입니다.");
        }

        // 비밀번호 암호화
        String encodedPassword = passwordEncoder.encode(password);

        // 새 사용자 생성
        User newUser = User.builder()
                .username(username)
                .name(name)
                .password(encodedPassword)
                .build();

        // DB에 저장
        User savedUser = userRepository.save(newUser);

        // 파일에도 저장
        saveToFile(savedUser, encodedPassword);

        return savedUser;
    }

    // user_data.txt 파일에 사용자 정보 저장
    private void saveToFile(User user, String encodedPassword) {
        try (BufferedWriter writer = new BufferedWriter(new FileWriter(USER_DATA_FILE, true))) {
            // 탭으로 구분된 형식: id	username	name	password	role
            String line = String.format("%d\t%s\t%s\t%s\t%s%n",
                    user.getId(),
                    user.getUsername(),
                    user.getName(),
                    encodedPassword,
                    user.getRole());
            writer.write(line);
            System.out.println("--- [파일 저장] user_data.txt에 사용자 정보 저장 완료: " + user.getUsername());
        } catch (IOException e) {
            System.err.println("--- [파일 저장 실패] user_data.txt 저장 중 오류 발생: " + e.getMessage());
            // 파일 저장 실패는 회원가입 자체를 실패시키지 않음 (DB에는 저장됨)
        }
    }
}