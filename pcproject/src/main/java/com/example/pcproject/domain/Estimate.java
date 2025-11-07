package com.example.pcproject.domain;

import jakarta.persistence.*;
import lombok.*;

import java.time.LocalDateTime;

@Entity
@Table(name = "estimate")
@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class Estimate {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    // 로그인한 사용자
    @Column(nullable = false)
    private Long userId;

    private String title;
    private Integer totalPrice;

    @Lob // JSON 전체 저장
    @Column(columnDefinition = "LONGTEXT")
    private String data;

    @Column(nullable = false)
    private LocalDateTime createdAt = LocalDateTime.now();
}
