package com.example.pcproject.repository;

import com.example.pcproject.domain.User;
import org.springframework.data.jpa.repository.JpaRepository;
import java.util.Optional;

public interface UserRepository extends JpaRepository<User, Long> {
    // Spring Security가 로그인 시 입력된 username으로 사용자를 찾을 때 사용
    Optional<User> findByUsername(String username);
}
